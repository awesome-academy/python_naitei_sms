import json
import random,string
import numpy as np
import os
import pandas as pd
from django.core.management.base import BaseCommand
from pitch.models import Pitch
from lorem_text import lorem
from django.contrib.staticfiles import finders
import xlwt
class Command(BaseCommand):
    help = 'Seed dữ liệu cho mô hình Pitch'

    def generate_random_phone(self):
        return f'{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}'

    def seed_pitches(self, num_pitches=6):
        pitches_data = []
        field_name = ['Anfield', 'Arsenal', 'Ayresome Park', 'Cardiff City', 'Bloomfield Road', 'Boundary Park']
        field_name_copy = field_name.copy()
        for i in range(1, num_pitches + 1):
            pitch_data = {
                'model': 'pitch.Pitch',
                'fields': {
                    'address': f'Address {i}',
                    'title': field_name_copy.pop(0),
                    'description': lorem.words(15),
                    'phone': self.generate_random_phone(),
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

    def seed_pitches_excel(self, num_pitches=6, num_images_per_pitch=3):
        pitches_data = []
        field_name = ['Anfield', 'Arsenal', 'Ayresome Park', 'Cardiff City', 'Bloomfield Road', 'Boundary Park']
        for i in range(1, num_pitches + 1):
            pitch_data = {
                'address': f'Address {i}',
                'title': random.choice(field_name),
                'description': lorem.words(15),
                'phone': self.generate_random_phone(),
                'size': random.choice(['1', '2', '3']),
                'surface': random.choice(['a', 'n', 'm']),
                'price': random.randint(1000, 10000),
            }
            for j in range(1, num_images_per_pitch + 1):
                pitch_data[f'image{j}'] = f'uploads/Pitch_img/Pitch_{i}/img_{j}.jpg'  # Đường dẫn hình ảnh
            pitches_data.append(pitch_data)
        return pitches_data


    def handle(self, *args, **kwargs):
        pitches_data = self.seed_pitches()
        images_data = self.seed_images()
        all_data = pitches_data + images_data
        json_file_path = os.path.join('pitch', 'fixtures', 'pitch_and_images_data.json')
        with open(json_file_path, 'w') as json_file:
            json.dump(all_data, json_file, indent=2)


        excel_file_path = os.path.join('static', 'Sample_data.xlsx')
        pitches_data_excel = self.seed_pitches_excel()

        df = pd.DataFrame(pitches_data_excel)
        df.to_excel(excel_file_path, index=False)
        wb = xlwt.Workbook(encoding="utf-8")
        ws = wb.add_sheet("PitchData")
        num_images_per_pitch = 3
        image_columns = [f"image{i}" for i in range(1, num_images_per_pitch + 1)]
        row_num = 0
        columns = [
            "address",
            "title",
            "description",
            "phone",
            "size",
            "surface",
            "price",
        ]+ image_columns

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num])

        for row in pitches_data_excel:
            row_num += 1
            for col_num in range(len(columns)):
                ws.write(row_num, col_num, row[columns[col_num]])

        wb.save(excel_file_path)
