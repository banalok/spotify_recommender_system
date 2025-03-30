import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.neighbors import NearestNeighbors
from dotenv import load_dotenv
import hopsworks
import os
import joblib

load_dotenv()

def main():
    hopsworks_api_key = os.getenv("HOPSWORKS_API_KEY")
    os.environ["HOPSWORKS_API_KEY"] = hopsworks_api_key
    
    # Log in to Hopsworks
    try:
        project = hopsworks.login()
    except Exception as e:
        print(f"Failed to login to Hopsworks: {e}")
        return
    
    # Retrieve feature group
    fs = project.get_feature_store()
    try:
        spotify_features = fs.get_feature_group(name="recommender_spotify", version=2)
        df = spotify_features.read()
    except Exception as e:
        print(f"Failed to retrieve feature group: {e}")
        return
    
    # Select and encode features
    selected_columns = ['popularity', 'artist_name', 'track_name']
    training_data = df[selected_columns].copy()
    
    label_encoder_artist = LabelEncoder()
    label_encoder_track = LabelEncoder()
    training_data['artist_encoded'] = label_encoder_artist.fit_transform(training_data['artist_name'])
    training_data['track_encoded'] = label_encoder_track.fit_transform(training_data['track_name'])
    
    features = ['popularity', 'artist_encoded', 'track_encoded']
    X = training_data[features]
    
    # Train KNN model
    knn_model = NearestNeighbors(n_neighbors=10, metric='cosine')
    knn_model.fit(X)  
    
    # Save the model
    model_dir = "./knn_model"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "knn_model.pkl")
    joblib.dump(knn_model, model_path)

    # Register model to Hopsworks
    try:
        mr = project.get_model_registry()
        model_name = "knn_recommendation_model_2"
        
        # Check if the model already exists
        try:
            existing_model = mr.get_model(name=model_name)
            print(f"Model '{model_name}' already exists in the Model Registry. Skipping registration.")
        except Exception as e:
            # Assuming that an exception is raised if the model does not exist
            print(f"Model '{model_name}' does not exist. Proceeding to register the model.")
            
            metrics = {
                "Number of neighbors": 10,
            }
            
            knn_recommendation_model = mr.python.create_model(
                name=model_name,       
                metrics=metrics,                       
                input_example=X.iloc[0].values,        
                description=(
                    "Content-based recommendation model using KNN. "
                    "This model uses cosine distance with 10 neighbors."
                ),
            )
            
            knn_recommendation_model.save(model_dir)
            print("KNN recommendation model has been saved to Hopsworks!")
    except Exception as e:
        print(f"Failed to register the model: {e}")

if __name__ == "__main__":
    main()