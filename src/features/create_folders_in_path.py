import os
import sys
import re

def main():
    args = sys.argv[1:]
    if not args:
        print("Error: Missing <folder_path> argument.")
        sys.exit(1)
    
    folder_path = args[0]
    
    if not os.path.exists(folder_path):
        print(f"Error: Thư mục '{folder_path}' không tồn tại.")
        sys.exit(1)

    user_pattern = None
    numbers_found = []

    for arg in args[1:]:
        if arg.isdigit():
            numbers_found.append(int(arg))
        else:
            user_pattern = arg

    starting_index = None
    num_folders = 1

    if len(numbers_found) == 1:
        starting_index = numbers_found[0]
    elif len(numbers_found) >= 2:
        starting_index = numbers_found[0]
        num_folders = numbers_found[1]

    # Find existing patterns
    existing_patterns = {}
    max_indices = {}
    regex = re.compile(r"^(.+)-(\d+)$")

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            match = regex.match(item)
            if match:
                pat = match.group(1)
                idx = int(match.group(2))
                if pat not in existing_patterns:
                    existing_patterns[pat] = 0
                existing_patterns[pat] += 1
                
                if pat not in max_indices or idx > max_indices[pat]:
                    max_indices[pat] = idx

    pattern_to_use = None
    if user_pattern:
        pattern_to_use = user_pattern
    else:
        if existing_patterns:
            # Chọn pattern có nhiều folder nhất
            pattern_to_use = max(existing_patterns.items(), key=lambda x: x[1])[0]
        else:
            pattern_to_use = "folder"
            
    index_to_use = 1
    if starting_index is not None:
        index_to_use = starting_index
    else:
        if pattern_to_use in max_indices:
            index_to_use = max_indices[pattern_to_use] + 1
        elif max_indices:
            # Nếu không tìm thấy index cho pattern được chọn nhưng có index của các pattern khác
            # (Trường hợp user nhập pattern mới, nhưng muốn tiếp tục chuỗi index chung?)
            # Prompt: "tìm index là số lớn nhất (nếu có) từ các folder con hiện tại... nếu ko tìm thấy thì bắt đầu từ 1"
            index_to_use = max(max_indices.values()) + 1
            
    for _ in range(num_folders):
        new_folder_name = f"{pattern_to_use}-{index_to_use}"
        new_folder_path = os.path.join(folder_path, new_folder_name)
        
        # Đảm bảo không ghi đè folder đã có
        while os.path.exists(new_folder_path):
            index_to_use += 1
            new_folder_name = f"{pattern_to_use}-{index_to_use}"
            new_folder_path = os.path.join(folder_path, new_folder_name)

        try:
            os.makedirs(new_folder_path)
            print(f"Created folder: {new_folder_path}")
        except Exception as e:
            print(f"Error creating folder: {e}")
            sys.exit(1)
            
        index_to_use += 1

if __name__ == "__main__":
    main()
