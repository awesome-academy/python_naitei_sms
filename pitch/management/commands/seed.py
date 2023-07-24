import json
import random
import numpy as np
import os
from django.core.management.base import BaseCommand
from pitch.models import Pitch

class Command(BaseCommand):
    help = 'Seed dữ liệu cho mô hình Pitch'

    def generate_random_phone(self):
        return f'{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}'
      
    def seed_pitches(self, num_pitches=6):
        pitches_data = []
        field_name = ['Anfield', 'Arsenal', 'Ayresome Park', 'Cardiff City', 'Bloomfield Road', 'Boundary Park']
        for i in range(1, num_pitches + 1):
            pitch_data = {
                'model': 'pitch.Pitch',
                'fields': {
                    'address': f'Address {i}',
                    'title': random.choice(field_name),
                    'description': f'Description for Pitch {i}',
                    'phone': self.generate_random_phone(),
                    'avg_rating': random.choice(np.arange(0,5,0.5)),
                    'size': random.choice(['1', '2', '3']),
                    'surface': random.choice(['a', 'n', 'm']),
                    'price': random.randint(1000, 10000),
                }
            }
            pitches_data.append(pitch_data)

        return pitches_data

    def seed_images(self, num_images=3):
        images_data = []
        # Tạo dữ liệu cho mô hình Pitch trước
        pitches_data = self.seed_pitches()
        # Lấy danh sách các đối tượng Pitch từ database
        pitches = Pitch.objects.all()
        for a in range(1, len(pitches_data) + 1 ):
            for i in range(1, num_images + 1):
                image_data = {
                    'model': 'pitch.Image',
                    'fields': {
                        'image': f'uploads/Pitch_img/Pitch_{a}/img_{i}.jpg',
                        'pitch': a,
                    }
                }
                images_data.append(image_data)
        return images_data

    def handle(self, *args, **kwargs):
        pitches_data = self.seed_pitches()
        images_data = self.seed_images()
        all_data = pitches_data + images_data

        # Create the file path
        file_path = os.path.join('pitch', 'fixtures', 'pitch_and_images_data.json')

        # Save all_data to a JSON file
        with open(file_path, 'w') as json_file:
            json.dump(all_data, json_file, indent=2)

