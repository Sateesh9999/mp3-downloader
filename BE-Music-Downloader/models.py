from pymongo import MongoClient
from config import get_config
from pymongo.server_api import ServerApi

config = get_config()
link = config.MONGO_URI
db = None
try:
    client = MongoClient(link, server_api=ServerApi('1'))
    db = client.music_downloader

  
# return a friendly error if a URI error is thrown 
except Exception as e:
    print("An error occurred while connecting to MongoDB:", e)  

class Playlist():
    """Store synced playlists"""

    def getPlaylists():
        return db['Playlist'].find()

    def getPlaylistById(playlist_id):
        return db['Playlist'].find_one({"_id": playlist_id})

    def getPlaylistByUrl(url):
        return db['Playlist'].find_one({"url": url})

    def addPlaylist(playlist):
        result = db['Playlist'].insert_one(playlist)
        playlist['_id'] = result.inserted_id
        return playlist

    def addTrackToPlaylist(playlist_id, track_id):
        result = db['Playlist'].update_one(
            {"_id": playlist_id},
            [
                {
                    "$set": {
                        "tracks": {
                            "$setUnion": [
                                {"$ifNull": ["$tracks", []]},
                                [track_id]
                            ] 
                        }
                    }
                },
                {
                    "$set": {
                        "track_count": {"$size": "$tracks"}
                    }
                }
            ]
        )
        return result.modified_count > 0

    def deletePlaylist(playlist_id):
        result = db['Playlist'].delete_one({"_id": playlist_id})
        return result.deleted_count > 0



class Track():
    """Store downloaded tracks"""

    @staticmethod
    def getTracks():
        return db['Track'].find()

    @staticmethod
    def getTracksByPlaylistId(playlist_id):
        # return db['Track'].find({"playlist_id": playlist_id})
        return db.Playlist.aggregate([
                    { "$match": { "_id": playlist_id } },
                    { "$lookup": {
                        "from": "Track", # Assuming your track collection is named "Track"
                        "localField": "tracks", # The array of track IDs in the playlist document
                        "foreignField": "_id", # The field in the tracks collection that matches those IDs
                        "as": "trackDetails" # The resulting array of full track documents
                    }},
                    {
                        "$unwind": "$trackDetails"
                    },
                    {
                        "$replaceRoot": {
                            "newRoot": "$trackDetails"
                        }
                    }
                ])

    @staticmethod
    def getTrackById(track_id):
        return db['Track'].find_one({"_id": track_id})

    @staticmethod
    def getTrackBySourceId(playlist_id, source_id):
        return db['Track'].find_one({"source_id": source_id})

    @staticmethod
    def getTracksPending(playlist_id, download_status='pending'):
        trackDetails = list(Track.getTracksByPlaylistId(playlist_id))
        tracks = []
        for track in trackDetails:
            if track['download_status'] == download_status:
                tracks.append(track)
        print(tracks)
        return tracks

    @staticmethod
    def addTrack(track):
        result = db['Track'].insert_one(track)
        track['_id'] = result.inserted_id
        return track


class SyncHistory():
    """Track all sync operations"""

    def addSyncHistory(sync_history):
        result = db['SyncHistory'].insert_one(sync_history)
        sync_history['_id'] = result.inserted_id
        return sync_history


class ScheduledSync():
    """Store scheduled sync configurations"""

    def getSchedulerConfig():
        return db['ScheduledSync'].find_one()

    def addSchedulerConfig(config_data):
        result = db['ScheduledSync'].insert_one(config_data)
        config_data['_id'] = result.inserted_id
        return config_data


