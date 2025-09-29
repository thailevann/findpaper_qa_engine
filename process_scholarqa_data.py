#!/usr/bin/env python3
"""
Script để xử lý dữ liệu ScholarQABench-base và tạo các file key_ingredients
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class ScholarQADataProcessor:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.metadata_file = self.base_dir / "original" / "qa_metadata_all (1).jsonl"
        self.snippets_file = self.base_dir / "original" / "output_snippets.jsonl"
        self.key_ingredients_dir = self.base_dir / "key_ingredients"
        
        # Tạo thư mục key_ingredients nếu chưa có
        self.key_ingredients_dir.mkdir(exist_ok=True)
    
    def load_metadata(self) -> Dict[int, Dict[str, Any]]:
        """Đọc metadata từ qa_metadata_all (1).jsonl"""
        metadata = {}
        
        print(f"Đang đọc metadata từ: {self.metadata_file}")
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    idx = data.get('idx')
                    if idx is not None:
                        metadata[idx] = data
                        print(f"Đã đọc metadata cho câu hỏi {idx}")
                except json.JSONDecodeError as e:
                    print(f"Lỗi JSON ở dòng {line_num}: {e}")
                    continue
        
        print(f"Tổng cộng đã đọc {len(metadata)} câu hỏi")
        return metadata
    
    def load_snippets(self) -> Dict[str, Dict[str, Any]]:
        """Đọc snippets từ output_snippets.jsonl"""
        snippets = {}
        
        print(f"Đang đọc snippets từ: {self.snippets_file}")
        
        with open(self.snippets_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    # Sử dụng question làm key để map với metadata
                    question = data.get('question', '')
                    if question:
                        snippets[question] = data
                except json.JSONDecodeError as e:
                    print(f"Lỗi JSON ở dòng {line_num}: {e}")
                    continue
        
        print(f"Tổng cộng đã đọc {len(snippets)} snippets")
        return snippets
    
    def create_key_ingredient_file(self, idx: int, content: str, file_suffix: str) -> str:
        """Tạo file key_ingredient với format {idx}_{suffix}.txt"""
        filename = f"{idx}_{file_suffix}.txt"
        filepath = self.key_ingredients_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(filepath)
    
    def process_question(self, metadata: Dict[str, Any], snippets: Dict[str, Dict[str, Any]]) -> List[str]:
        """Xử lý một câu hỏi và tạo các file key_ingredients"""
        idx = metadata.get('idx')
        question = metadata.get('question', '')
        
        if not idx or not question:
            print(f"Thiếu thông tin cần thiết cho câu hỏi: {metadata}")
            return []
        
        print(f"\nĐang xử lý câu hỏi {idx}: {question[:100]}...")
        
        created_files = []
        
        # Tạo file 1: Question và Most Important ingredients
        content_1 = self._create_content_1(metadata, snippets.get(question, {}))
        if content_1:
            file_1 = self.create_key_ingredient_file(idx, content_1, "1")
            created_files.append(file_1)
            print(f"Đã tạo file: {file_1}")
        
        # Tạo file 2: Nice to have ingredients
        content_2 = self._create_content_2(metadata, snippets.get(question, {}))
        if content_2:
            file_2 = self.create_key_ingredient_file(idx, content_2, "2")
            created_files.append(file_2)
            print(f"Đã tạo file: {file_2}")
        
        return created_files
    
    def _create_content_1(self, metadata: Dict[str, Any], snippets: Dict[str, Any]) -> str:
        """Tạo nội dung cho file {idx}_1.txt (Most Important)"""
        content = []
        
        # Question
        content.append("Question")
        content.append("")
        content.append(metadata.get('question', ''))
        content.append("")
        content.append("")
        content.append("")
        content.append("")
        content.append("")
        
        # Most Important
        content.append("Most Important")
        content.append("")
        
        # Lấy ingredients từ snippets nếu có
        if snippets and 'ingredients' in snippets:
            ingredients = snippets['ingredients']
            most_important = ingredients.get('most_important', [])
            
            for item in most_important:
                text = item.get('text', '')
                if text:
                    content.append(f"* {text}")
                    content.append("")
                    
                    # Supporting quotes
                    content.append("Supporting quotes")
                    content.append("")
                    
                    snippets_list = item.get('snippets', [])
                    for snippet in snippets_list:
                        content.append(f'"{snippet}"')
                        content.append("")
                    
                    content.append("")
                    content.append("")
                    content.append("")
                    content.append("")
        
        return "\n".join(content)
    
    def _create_content_2(self, metadata: Dict[str, Any], snippets: Dict[str, Any]) -> str:
        """Tạo nội dung cho file {idx}_2.txt (Nice to have)"""
        content = []
        
        # Question
        content.append("Question")
        content.append("")
        content.append(metadata.get('question', ''))
        content.append("")
        content.append("")
        content.append("")
        content.append("")
        content.append("")
        
        # Nice to have
        content.append("Nice to have")
        content.append("")
        
        # Lấy ingredients từ snippets nếu có
        if snippets and 'ingredients' in snippets:
            ingredients = snippets['ingredients']
            nice_to_have = ingredients.get('nice_to_have', [])
            
            for item in nice_to_have:
                text = item.get('text', '')
                if text:
                    content.append(f"* {text}")
                    content.append("")
                    
                    # Supporting quotes
                    content.append("Supporting quotes")
                    content.append("")
                    
                    snippets_list = item.get('snippets', [])
                    for snippet in snippets_list:
                        content.append(f'"{snippet}"')
                        content.append("")
                    
                    content.append("")
                    content.append("")
                    content.append("")
                    content.append("")
        
        return "\n".join(content)
    
    def process_all(self):
        """Xử lý tất cả dữ liệu"""
        print("Bắt đầu xử lý dữ liệu ScholarQABench-base...")
        
        # Đọc metadata
        metadata = self.load_metadata()
        if not metadata:
            print("Không tìm thấy metadata!")
            return
        
        # Đọc snippets
        snippets = self.load_snippets()
        
        # Xử lý từng câu hỏi
        total_processed = 0
        total_files_created = 0
        
        for idx, meta in metadata.items():
            try:
                created_files = self.process_question(meta, snippets)
                total_files_created += len(created_files)
                total_processed += 1
                
                if total_processed % 10 == 0:
                    print(f"Đã xử lý {total_processed} câu hỏi...")
                    
            except Exception as e:
                print(f"Lỗi khi xử lý câu hỏi {idx}: {e}")
                continue
        
        print(f"\nHoàn thành! Đã xử lý {total_processed} câu hỏi và tạo {total_files_created} file.")
        print(f"Các file được lưu trong: {self.key_ingredients_dir}")

def main():
    # Đường dẫn đến thư mục ScholarQABench-base
    base_dir = "evaluation/ScholarQABench-base"
    
    # Kiểm tra thư mục có tồn tại không
    if not os.path.exists(base_dir):
        print(f"Không tìm thấy thư mục: {base_dir}")
        return
    
    # Tạo processor và xử lý
    processor = ScholarQADataProcessor(base_dir)
    processor.process_all()

if __name__ == "__main__":
    main()

