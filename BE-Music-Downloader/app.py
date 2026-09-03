import os
from flask.json.provider import DefaultJSONProvider
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from io import BytesIO
from bson import ObjectId

# Import configuration and models
from config import get_config
from models import db, Playlist, Track, SyncHistory, ScheduledSync
from services import SyncService

class MongoJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return super().default(o)

def create_app(config_name=None):
    """Application factory"""
    app = Flask(__name__)

    app.json = MongoJSONProvider(app)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize database
    # db.init_app(app)
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": [app.config['FRONTEND_ORIGIN']]
        }
    })
    
    # Create tables
    # with app.app_context():
    #     db.create_all()
    
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.start()
    
    # --- API Routes: Playlist Management ---
    
    @app.route('/api/playlists', methods=['GET'])
    def get_playlists():
        """Get all synced playlists"""
        try:
            playlists = Playlist.getPlaylists()
            playlists_list = list(playlists)
            return jsonify({
                'status': 'success',
                'playlists': playlists_list,
                'count': len(playlists_list)
            }), 200
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/playlists', methods=['POST'])
    def add_playlist():
        """Add a new playlist to sync"""
        try:
            if not request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid request format. Must be JSON.'}), 400
            
            data = request.get_json()
            url = data.get('url')
            
            if not url:
                return jsonify({'status': 'error', 'message': "Missing 'url' in request body"}), 400
            
            # Add playlist using sync service
            success, message, playlist = SyncService.add_playlist(
                url,
                app.config['DEST_DIR']
            )
            
            if success:
                sync_single_playlist(playlist['_id'])
                return jsonify({
                    'status': 'success',
                    'message': message,
                    'playlist': playlist
                }), 201
            else:
                return jsonify({'status': 'error', 'message': message}), 400
                
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/playlists/<string:playlist_id>', methods=['GET'])
    def get_playlist_details(playlist_id):
        """Get detailed information about a playlist"""
        try:
            playlist_id = ObjectId(playlist_id)
            details = SyncService.get_playlist_details(playlist_id)
            
            if not details:
                return jsonify({'status': 'error', 'message': 'Playlist not found'}), 404
            
            return jsonify({
                'status': 'success',
                'data': details
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/playlists/<string:playlist_id>', methods=['DELETE'])
    def delete_playlist(playlist_id):
        """Delete a playlist from sync"""
        try:
            playlist_id = ObjectId(playlist_id)
            data = request.get_json() if request.is_json else {}
            delete_files = data.get('delete_files', False)
            
            success, message = SyncService.delete_playlist(playlist_id, delete_files)
            
            status_code = 200 if success else 400
            return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # --- API Routes: Sync Control ---
    
    @app.route('/api/sync/playlist/<string:playlist_id>', methods=['POST'])
    def sync_single_playlist(playlist_id):
        """Manually sync a single playlist"""
        try:
            playlist_id = ObjectId(playlist_id)
            success, message, history = SyncService.sync_playlist(
                playlist_id,
                app.config['DOWNLOAD_TIMEOUT']
            )
            
            status_code = 200 if success else 500
            response = {
                'status': 'success' if success else 'error',
                'message': message
            }
            
            if history:
                response['sync_history'] = history
            
            return jsonify(response), status_code
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sync/all', methods=['POST'])
    def sync_all_playlists():
        """Manually sync all playlists"""
        try:
            success, message, histories = SyncService.sync_all_playlists(
                app.config['DOWNLOAD_TIMEOUT']
            )
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': message,
                'sync_histories': histories
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sync/history', methods=['GET'])
    def get_sync_history():
        """Get sync history"""
        try:
            playlist_id_str = request.args.get('playlist_id', type=str)
            
            if playlist_id_str:
                playlist_id = ObjectId(playlist_id_str)
                # MongoDB query: find and sort by start_time descending
                histories = list(db['SyncHistory'].find({'playlist_id': playlist_id}).sort('start_time', -1))
            else:
                # Get all histories if no playlist_id provided
                histories = list(db['SyncHistory'].find({}).sort('start_time', -1))
            
            return jsonify({
                'status': 'success',
                'sync_histories': histories
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/sync/status', methods=['GET'])
    def get_sync_status():
        """Get current sync status of all playlists"""
        try:
            playlists = Playlist.getPlaylists()
            
            status_info = []
            for p in playlists:
                status_info.append({
                    'id': p['_id'],
                    'name': p['name'],
                    'sync_status': p['sync_status'],
                    'last_sync_time': p['last_sync_time'].isoformat() if p['last_sync_time'] else None,
                    'track_count': p['track_count']
                })
            
            return jsonify({
                'status': 'success',
                'playlists': status_info
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # --- API Routes: Streaming & Download ---
    
    @app.route('/api/stream/<string:track_id>', methods=['GET'])
    def stream_track(track_id):
        """Stream audio from server"""
        try:
            track_id = ObjectId(track_id)
            track = Track.getTrackById(track_id)
            
            if not track:
                return jsonify({'status': 'error', 'message': 'Track not found'}), 404
            
            if not track['file_path'] or not os.path.exists(track['file_path']):
                return jsonify({'status': 'error', 'message': 'Track file not found'}), 404
            
            return send_file(
                track['file_path'],
                mimetype='audio/mpeg',
                as_attachment=False
            )
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/download/<string:track_id>', methods=['GET'])
    def download_track(track_id):
        """Download track file to mobile"""
        try:
            track_id = ObjectId(track_id)
            track = Track.getTrackById(track_id)
            
            if not track:
                return jsonify({'status': 'error', 'message': 'Track not found'}), 404
            
            if not track['file_path'] or not os.path.exists(track['file_path']):
                return jsonify({'status': 'error', 'message': 'Track file not found'}), 404
            
            return send_file(
                track['file_path'],
                mimetype='audio/mpeg',
                as_attachment=True,
                download_name=track['filename'] or 'track.mp3'
            )
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # --- API Routes: Scheduler Management ---
    
    @app.route('/api/scheduler/config', methods=['GET'])
    def get_scheduler_config():
        """Get current scheduler configuration"""
        try:
            config = ScheduledSync.getSchedulerConfig()
            
            if not config:
                # Create default config
                config = ScheduledSync.addSchedulerConfig({
                    'enabled': True,
                    'day_of_week': 0,
                    'time_of_day': '02:00',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'last_run': None,
                    'next_run': None
                })
            
            return jsonify({
                'status': 'success',
                'config': config
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/scheduler/config', methods=['POST'])
    def update_scheduler_config():
        """Update scheduler configuration"""
        try:
            if not request.is_json:
                return jsonify({'status': 'error', 'message': 'Invalid request format'}), 400
            
            data = request.get_json()
            
            config = ScheduledSync.getSchedulerConfig()
            if not config:
                config = ScheduledSync.addSchedulerConfig({
                    'enabled': True,
                    'day_of_week': 0,
                    'time_of_day': '02:00',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow(),
                    'last_run': None,
                    'next_run': None
                })

            if 'enabled' in data:
                db['ScheduledSync'].update_one({'_id': config['_id']}, {'$set': {
                    'enabled': data['enabled']
                }})
                config['enabled'] = data['enabled']
            if 'day_of_week' in data:
                db['ScheduledSync'].update_one({'_id': config['_id']}, {'$set': {
                    'day_of_week': data['day_of_week']
                }})
                config['day_of_week'] = data['day_of_week']
            if 'time_of_day' in data:
                db['ScheduledSync'].update_one({'_id': config['_id']}, {'$set': {
                    'time_of_day': data['time_of_day']
                }})
                config['time_of_day'] = data['time_of_day']
            
            db['ScheduledSync'].update_one({'_id': config['_id']}, {'$set': {
                'updated_at': datetime.utcnow()
            }})
            config['updated_at'] = datetime.utcnow()
            
            
            # Update scheduler job
            _update_scheduler_job(app, scheduler, config)
            
            return jsonify({
                'status': 'success',
                'message': 'Scheduler updated',
                'config': config
            }), 200
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # --- Health Check ---
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'success',
            'message': 'Server is running',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    # --- Scheduler Job ---
    
    def scheduled_sync_job():
        """Job to run automatic sync"""
        with app.app_context():
            print(f"[{datetime.utcnow()}] Running scheduled sync...")
            success, message, _ = SyncService.sync_all_playlists(
                app.config['DOWNLOAD_TIMEOUT']
            )
            print(f"[{datetime.utcnow()}] Scheduled sync completed: {message}")
    
    def _update_scheduler_job(app, scheduler, config):
        """Update the scheduler job based on configuration"""
        # Remove existing job if present
        if scheduler.get_job('auto_sync'):
            scheduler.remove_job('auto_sync')
        
        # Add new job if enabled
        if config['enabled']:
            from apscheduler.triggers.cron import CronTrigger
            
            # Parse time of day (HH:MM format)
            hour, minute = map(int, config['time_of_day']   .split(':'))
            
            trigger = CronTrigger(
                day_of_week=config['day_of_week'],
                hour=hour,
                minute=minute
            )
            
            scheduler.add_job(
                scheduled_sync_job,
                trigger=trigger,
                id='auto_sync',
                name='Automatic weekly sync',
                replace_existing=True
            )
            
            print(f"Scheduler updated: Weekly sync on day {config['day_of_week']} at {config['time_of_day']}")
    
    # Initialize scheduler on startup
    with app.app_context():
        config_obj = ScheduledSync.getSchedulerConfig()
        if config_obj:
            _update_scheduler_job(app, scheduler, config_obj)
    
    return app


# Create and run the app
if __name__ == '__main__':
    app = create_app()
    
    port = app.config.get('BACKEND_PORT', 5000)
    print(f"Flask Server running on http://127.0.0.1:{port}")
    print(f"Frontend origin: {app.config.get('FRONTEND_ORIGIN')}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )