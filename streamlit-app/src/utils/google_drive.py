import os
import json
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import dotenv

dotenv.load_dotenv(".env")


class GoogleDriveManager:
    def __init__(self, credentials_env_var='GDRIVE_CREDENTIALS', scopes=None):
        # Default to a common scope for Drive if none provided
        if scopes is None:
            scopes = ['https://www.googleapis.com/auth/drive']
        
        # Load service account credentials from environment variable
        credentials_data = os.environ.get(credentials_env_var)

        print(credentials_data)
        if not credentials_data:
            raise ValueError(f"Environment variable {credentials_env_var} not set or empty.")
        
        service_account_info = json.loads(credentials_data)
        print(service_account_info)
        creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
        
        self.service = build('drive', 'v3', credentials=creds)

    def list_files_in_directory(self, folder_id):
        """
        Lists all files (not subfolders) in the specified folder.
        
        Args:
            folder_id (str): The ID of the folder whose contents you want to list.
        
        Returns:
            list of dict: A list of file metadata dictionaries.
        """
        query = f"'{folder_id}' in parents and trashed=false"
        page_token = None
        files = []

        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType)',
                pageToken=page_token
            ).execute()
            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if page_token is None:
                break

        return files

    def get_file_id_by_name(self, folder_id, filename):
        """
        Given a folder ID and a filename, returns the file ID if it exists.
        
        Args:
            folder_id (str): ID of the folder to search in.
            filename (str): The name of the file you're looking for.
        
        Returns:
            str or None: The file ID if found, otherwise None.
        """
        files = self.list_files_in_directory(folder_id)
        for f in files:
            if f['name'] == filename:
                return f['id']
        return None

    def create_directory(self, name, parent_folder_id=None):
        """
        Creates a new directory (folder) in Google Drive.
        
        Args:
            name (str): The name of the folder to create.
            parent_folder_id (str, optional): Parent folder ID. If omitted, folder is created in root.
        
        Returns:
            str: The newly created folder's ID.
        """
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')

    def upload_file_to_directory(self, file_path, folder_id, mime_type='application/json'):
        """
        Uploads a file from the local filesystem to the specified folder in Google Drive.
        
        Args:
            file_path (str): Path to the local file.
            folder_id (str): ID of the folder to upload the file into.
            mime_type (str, optional): MIME type of the file. Defaults to 'application/json'.
        
        Returns:
            str: The file ID of the uploaded file.
        """
        file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    def download_file(self, file_id, destination_path):
        """
        Downloads a file from Google Drive by its file ID.
        
        Args:
            file_id (str): The ID of the file to be downloaded.
            destination_path (str): The local path where the file should be saved.
        
        Returns:
            str: The local path of the downloaded file.
        """
        request = self.service.files().get_media(fileId=file_id)
        
        # If destination directory doesn't exist, create it
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)

        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download {int(status.progress() * 100)}%.")

        fh.close()
        return destination_path


if __name__ == "__main__":
    # Example usage:
    drive_manager = GoogleDriveManager()

    # Suppose we know the folder ID
    folder_id = '1Sp_gh2BFZrsCLnYK061iGm_qow8xmSYk'

    # List files in the folder
    files = drive_manager.list_files_in_directory(folder_id)
    print("Files in folder:", files)

    # Let's say we want to find the file_id of a file named 'progress.json'
    filename = "progress.json"
    file_id = drive_manager.get_file_id_by_name(folder_id, filename)
    if file_id:
        print(f"File '{filename}' found with ID: {file_id}")
        # Download it
        downloaded_path = drive_manager.download_file(file_id, "downloads/progress_downloaded.json")
        print("File downloaded to:", downloaded_path)
    else:
        print(f"File '{filename}' not found in the directory.")
