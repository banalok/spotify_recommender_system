import hopsworks
import os
from sklearn.preprocessing import LabelEncoder
import joblib
import streamlit as st
import hopsworks
import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors

def get_recommendations(top_tracks):
    """Get song recommendations by training a KNN model on the fly."""
    try:
        # Connect to Hopsworks
        os.environ["HOPSWORKS_API_KEY"] = st.secrets["hopsworks"]["api_key"]
        project = hopsworks.login()
        
        # Get feature data
        fs = project.get_feature_store()
        spotify_features = fs.get_feature_group(name="recommender_spotify", version=2)
        df = spotify_features.read()
        
        # Prepare data
        selected_columns = ['popularity', 'artist_name', 'track_name']
        training_data = df[selected_columns].copy()
        
        # Encode features
        label_encoder_artist = LabelEncoder()
        label_encoder_track = LabelEncoder()
        training_data['artist_encoded'] = label_encoder_artist.fit_transform(training_data['artist_name'])
        training_data['track_encoded'] = label_encoder_track.fit_transform(training_data['track_name'])
        
        # Train KNN model directly
        features = training_data[['popularity', 'artist_encoded', 'track_encoded']]
        knn_model = NearestNeighbors(n_neighbors=10, metric='cosine')
        knn_model.fit(features)
        
        # Process user tracks
        training_data['track_name'] = training_data['track_name'].str.strip().str.lower()
        user_tracks = [track["name"].strip().lower() for track in top_tracks]
        filtered_tracks = training_data[training_data['track_name'].isin(user_tracks)]
        
        if filtered_tracks.empty:
            print("No matching tracks found. Using popularity-based recommendations.")
            return training_data.sort_values(by='popularity', ascending=False).head(10)[['track_name', 'artist_name']]
        
        # Generate recommendations
        user_features = filtered_tracks[['popularity', 'artist_encoded', 'track_encoded']]
        distances, indices = knn_model.kneighbors(user_features, n_neighbors=10)
        
        # Collect unique recommendations
        all_indices = indices.flatten()
        unique_indices = []
        for idx in all_indices:
            if idx not in unique_indices:
                unique_indices.append(idx)
                if len(unique_indices) >= 10:
                    break
        
        recommendations = training_data.iloc[unique_indices]
        return recommendations[['track_name', 'artist_name']]
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise Exception(f"Error getting recommendations: {str(e)}")