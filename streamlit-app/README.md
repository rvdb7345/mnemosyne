# Streamlit Application

This project is a Streamlit application designed for language practice, allowing users to upload exercises, track their progress, and reset their progress as needed.

## Project Structure

```
streamlit-app
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── pages
│   │   ├── __init__.py
│   │   ├── home.py
│   │   ├── practice.py
│   │   ├── upload_exercise.py
│   │   └── reset_progress.py
│   ├── utils
│   │   ├── __init__.py
│   │   └── helpers.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd streamlit-app
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
streamlit run src/main.py
```

## Features

- **Home Page**: Overview and navigation to other functionalities.
- **Practice**: Engage with exercises and track your progress.
- **Upload Exercise**: Upload new exercises in TXT or CSV format.
- **Reset Progress**: Reset your progress with a confirmation step.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.