
import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html, Input, Output, State
import os

# --- 0. Configuration ---
IMAGE_ARCHIVE_BASE = "/Volumes/MediaVault/Masters/Camelot_Photos"

# --- 1. Data Loading and Preparation ---
def load_and_prepare_data():
    """
    Loads base, missing, and manual data, then merges them.
    Manual entries overwrite base data to ensure corrections are applied.
    Constructs the full path for each image file.
    """
    base_path = os.path.dirname(__file__)
    try:
        # Load the main dataset
        df_base = pd.read_csv(os.path.join(base_path, 'temperature_data.csv'))

        # Load supplementary datasets
        df_missing = pd.read_csv(os.path.join(base_path, 'missing_temperature_data.csv'))
        df_manual = pd.read_csv(os.path.join(base_path, 'manual_extreme_temperature_entries.csv'))

        # Combine all dataframes
        df_combined = pd.concat([df_base, df_missing, df_manual], ignore_index=True)

        # The 'filename' column is the unique identifier for an observation.
        # We sort by 'confidence' so that manual entries (confidence=1.0) are preferred.
        # When dropping duplicates, the last entry is kept, which will be the manual one if present.
        df_combined = df_combined.sort_values('confidence', ascending=True)
        df_final = df_combined.drop_duplicates(subset='filename', keep='last').copy()

        # Construct the full path
        df_final['full_path'] = df_final.apply(
            lambda row: os.path.join(IMAGE_ARCHIVE_BASE, row['deployment_id'], row['filename']),
            axis=1
        )

        # Convert timestamp to datetime objects for plotting
        df_final.loc[:, 'timestamp'] = pd.to_datetime(df_final['timestamp'], format='%Y%m%d%H%M%S', errors='coerce')

        # Drop rows where timestamp conversion failed and sort
        df_final = df_final.dropna(subset=['timestamp']).sort_values('timestamp')

        return df_final

    except FileNotFoundError as e:
        print(f"Error loading data: {e}. Make sure all required CSV files are in the same directory.")
        return pd.DataFrame()

# Load data once globally
master_df = load_and_prepare_data()
if master_df.empty:
    exit("Could not load data. Exiting.")

# --- 2. Dash App Initialization ---
app = dash.Dash(__name__, title="Manual Temperature Review")

# --- 3. App Layout ---
app.layout = html.Div([
    html.H1("Manual Temperature Data Review", style={'textAlign': 'center'}),
    html.P(
        "Select a deployment, click on points to mark/unmark them for follow-up, then click save.",
        style={'textAlign': 'center'}
    ),

    dcc.Dropdown(
        id='deployment-dropdown',
        options=[{'label': i, 'value': i} for i in sorted(master_df['deployment_id'].unique())],
        placeholder="Select a deployment...",
        style={'width': '50%', 'margin': '0 auto'}
    ),

    dcc.Graph(id='temperature-plot'),

    html.Div([
        html.Button('Save Marked Points', id='save-button', n_clicks=0),
    ], style={'textAlign': 'center', 'marginTop': '20px'}),

    html.Div(id='save-status', style={'textAlign': 'center', 'marginTop': '10px', 'color': 'green'}),

    # Store for client-side data
    dcc.Store(id='marked-points-store', data={})
])

# --- 4. Callbacks ---
@app.callback(
    Output('temperature-plot', 'figure'),
    Output('marked-points-store', 'data'),
    Input('deployment-dropdown', 'value'),
    Input('marked-points-store', 'data'),
    Input('temperature-plot', 'clickData')
)
def update_plot_and_store(deployment_id, stored_data, clickData):
    """
    Handles updating the plot based on dropdown selection and clicks.
    Manages the state of marked points.
    """
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # If a new deployment is selected, filter data and reset the store
    if trigger_id == 'deployment-dropdown':
        if not deployment_id:
            return go.Figure(), {}
        
        deployment_df = master_df[master_df['deployment_id'] == deployment_id].copy()
        deployment_df['color'] = 'blue' # Default color
        stored_data = deployment_df.to_dict('records')
    
    # If no data is loaded yet, do nothing
    if not stored_data:
        return go.Figure(layout={'title': 'Please select a deployment'}), {}

    # If a point is clicked, toggle its color and update the store
    if trigger_id == 'temperature-plot' and clickData:
        point_index = clickData['points'][0]['pointIndex']
        
        # Toggle the 'marked' state
        if stored_data[point_index].get('marked', False):
            stored_data[point_index]['color'] = 'blue'
            stored_data[point_index]['marked'] = False
        else:
            stored_data[point_index]['color'] = 'red'
            stored_data[point_index]['marked'] = True

    # Create the figure from the (potentially updated) stored data
    plot_df = pd.DataFrame(stored_data)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=plot_df['timestamp'],
        y=plot_df['temperature'],
        mode='markers',
        marker=dict(color=plot_df['color']),
        customdata=plot_df['filename'] # Pass filename for context
    ))
    fig.update_layout(
        title=f'Temperature for Deployment: {deployment_id}',
        xaxis_title='Timestamp',
        yaxis_title='Temperature (°F)',
        transition_duration=200
    )
    return fig, stored_data


@app.callback(
    Output('save-status', 'children'),
    Input('save-button', 'n_clicks'),
    State('deployment-dropdown', 'value'),
    State('marked-points-store', 'data')
)
def save_marked_points(n_clicks, deployment_id, stored_data):
    """Saves the points marked for follow-up to a CSV file."""
    if n_clicks == 0 or not deployment_id or not stored_data:
        return ""

    marked_df = pd.DataFrame(stored_data)
    follow_up_df = marked_df[marked_df.get('marked', False) == True]

    if follow_up_df.empty:
        return f"No points marked for deployment {deployment_id}. Nothing to save."

    # Define column order for export
    export_columns = [
        'filename', 'full_path', 'deployment_id', 'timestamp',
        'temperature', 'confidence', 'extraction_status'
    ]
    
    # Clean up for export, ensuring all required columns are present
    export_df = follow_up_df.copy()
    for col in ['color', 'marked']:
        if col in export_df.columns:
            export_df = export_df.drop(columns=[col])

    # Reorder columns
    export_df = export_df[export_columns]
    
    output_filename = f"{deployment_id}_followup.csv"
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    
    export_df.to_csv(output_path, index=False)
    
    return f"Successfully saved {len(export_df)} points to {output_filename}"

# --- 5. Run the App ---
if __name__ == '__main__':
    if master_df.empty:
        print("Could not start the application because data loading failed.")
    else:
        app.run(debug=True)
