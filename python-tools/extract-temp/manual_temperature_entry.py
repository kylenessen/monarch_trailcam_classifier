#!/usr/bin/env python3
"""
Simple manual temperature entry tool for trail camera images.
Usage: python manual_temperature_entry.py missing_temperature_images.csv
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from PIL import Image, ImageTk
import argparse
import sys
from pathlib import Path


class TemperatureEntryApp:
    def __init__(self, csv_path):
        # Load image data
        self.df = pd.read_csv(csv_path)
        self.current_index = 0
        self.results = []
        
        # Setup main window
        self.root = tk.Tk()
        self.root.title("Manual Temperature Entry")
        self.root.geometry("1000x800")
        
        # Create UI elements
        self.setup_ui()
        
        # Load first image
        self.load_current_image()
        
        # Setup key bindings
        self.root.bind('<Return>', self.next_image)
        self.root.bind('<Left>', self.previous_image)
        self.root.bind('<Right>', self.next_image)
        self.root.focus_set()
        
    def setup_ui(self):
        # Progress label
        self.progress_label = tk.Label(
            self.root, 
            text="", 
            font=('Arial', 14, 'bold')
        )
        self.progress_label.pack(pady=10)
        
        # Image display
        self.image_label = tk.Label(self.root)
        self.image_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(
            self.root,
            text="Enter temperature in Celsius (°C). Use arrow keys or Enter to navigate.",
            font=('Arial', 12)
        )
        instructions.pack(pady=5)
        
        # Temperature entry frame
        entry_frame = tk.Frame(self.root)
        entry_frame.pack(pady=20)
        
        tk.Label(entry_frame, text="Temperature (°C):", font=('Arial', 14)).pack(side=tk.LEFT, padx=5)
        
        self.temp_entry = tk.Entry(
            entry_frame, 
            font=('Arial', 16), 
            width=10,
            justify='center'
        )
        self.temp_entry.pack(side=tk.LEFT, padx=5)
        self.temp_entry.focus()
        
        # Navigation buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)
        
        self.prev_button = tk.Button(
            button_frame,
            text="← Previous",
            command=self.previous_image,
            font=('Arial', 12)
        )
        self.prev_button.pack(side=tk.LEFT, padx=10)
        
        self.next_button = tk.Button(
            button_frame,
            text="Next →",
            command=self.next_image,
            font=('Arial', 12)
        )
        self.next_button.pack(side=tk.LEFT, padx=10)
        
        # Save button
        save_button = tk.Button(
            self.root,
            text="Save All Results",
            command=self.save_results,
            font=('Arial', 14, 'bold'),
            bg='green',
            fg='white'
        )
        save_button.pack(pady=20)
        
    def load_current_image(self):
        if self.current_index >= len(self.df):
            self.finish_entry()
            return
            
        # Update progress
        progress_text = f"Image {self.current_index + 1} of {len(self.df)}"
        self.progress_label.config(text=progress_text)
        
        # Get current image info
        row = self.df.iloc[self.current_index]
        image_path = row['full_path']
        
        # Display filename
        filename_text = f"File: {row['filename']} (Deployment: {row['deployment_id']})"
        self.root.title(f"Manual Temperature Entry - {filename_text}")
        
        # Load and display image
        try:
            print(f"Attempting to load: {image_path}")
            print(f"Path exists: {Path(image_path).exists()}")
            
            img = Image.open(image_path)
            print(f"Image loaded successfully, size: {img.size}, mode: {img.mode}")
            
            # Resize image to fit screen while maintaining aspect ratio
            max_width, max_height = 800, 500
            img.thumbnail((max_width, max_height))  # Remove resample argument for now
            print(f"Thumbnail created, new size: {img.size}")
            
            # Convert to PhotoImage - save to temp file method
            import tempfile
            import os
            
            # Save to temporary file and load with tkinter
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(tmp_path, 'PNG')
            
            # Load with tkinter PhotoImage
            photo = tk.PhotoImage(file=tmp_path)
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Keep a reference
            print("Image displayed successfully")
            
        except Exception as e:
            error_msg = f"Error loading image: {e}\nPath: {image_path}"
            print(error_msg)
            self.image_label.config(text=error_msg)
            
        # Clear entry and focus
        self.temp_entry.delete(0, tk.END)
        self.temp_entry.focus()
        
        # Load existing value if we've been here before
        if self.current_index < len(self.results):
            existing_temp = self.results[self.current_index].get('temperature')
            if existing_temp is not None:
                self.temp_entry.insert(0, str(existing_temp))
                
        # Update button states
        self.prev_button.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
        
    def next_image(self, event=None):
        # Save current temperature
        self.save_current_temperature()
        
        # Move to next image
        if self.current_index < len(self.df) - 1:
            self.current_index += 1
            self.load_current_image()
        else:
            self.finish_entry()
            
    def previous_image(self, event=None):
        if self.current_index > 0:
            # Save current temperature
            self.save_current_temperature()
            
            # Move to previous image
            self.current_index -= 1
            self.load_current_image()
            
    def save_current_temperature(self):
        # Get temperature value
        temp_text = self.temp_entry.get().strip()
        
        # Validate temperature
        try:
            temperature = float(temp_text) if temp_text else None
            if temperature is not None and (temperature < -50 or temperature > 60):
                messagebox.showwarning("Warning", f"Temperature {temperature}°C seems unusual. Double-check if this is correct.")
        except ValueError:
            if temp_text:  # Only warn if they entered something
                messagebox.showerror("Error", f"Invalid temperature: '{temp_text}'. Please enter a number.")
                return
            temperature = None
            
        # Get current row data
        row = self.df.iloc[self.current_index]
        
        # Create result entry
        result = {
            'filename': row['filename'],
            'deployment_id': row['deployment_id'], 
            'timestamp': row['timestamp'],
            'temperature': temperature,
            'confidence': 1.0,  # Manual entry has perfect confidence
            'extraction_status': 'manual_entry'
        }
        
        # Update or append result
        if self.current_index < len(self.results):
            self.results[self.current_index] = result
        else:
            # Fill any gaps with None results
            while len(self.results) <= self.current_index:
                self.results.append(None)
            self.results[self.current_index] = result
            
    def save_results(self):
        # Save current temperature before saving all
        self.save_current_temperature()
        
        # Filter out None results and create DataFrame
        valid_results = [r for r in self.results if r is not None and r['temperature'] is not None]
        
        if not valid_results:
            messagebox.showwarning("Warning", "No temperatures entered yet.")
            return
            
        # Create output DataFrame
        output_df = pd.DataFrame(valid_results)
        
        # Save to CSV
        output_path = "manual_temperature_entries.csv"
        output_df.to_csv(output_path, index=False)
        
        completed = len(valid_results)
        total = len(self.df)
        
        messagebox.showinfo(
            "Results Saved", 
            f"Saved {completed} of {total} temperature entries to {output_path}"
        )
        
    def finish_entry(self):
        # Save any remaining temperature
        self.save_current_temperature()
        
        # Show completion dialog
        completed = len([r for r in self.results if r is not None and r.get('temperature') is not None])
        total = len(self.df)
        
        if completed == total:
            message = f"All {total} temperatures entered! Great work!"
        else:
            message = f"Completed {completed} of {total} images.\nYou can continue later or save current progress."
            
        result = messagebox.askyesno(
            "Entry Complete", 
            f"{message}\n\nSave results now?"
        )
        
        if result:
            self.save_results()
            
        self.root.quit()
        
    def run(self):
        self.root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Manual temperature entry for trail camera images")
    parser.add_argument("csv_path", help="Path to CSV file containing image paths")
    
    args = parser.parse_args()
    
    # Check if CSV exists
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
        
    # Start the application
    app = TemperatureEntryApp(args.csv_path)
    app.run()


if __name__ == "__main__":
    main()