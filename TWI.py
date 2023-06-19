import os

directory = "/home/dryfrost/Desktop/HUCS"  # Replace with the directory path where the .tif files are located


tif_files = []

for file in os.listdir(directory):
    if file.endswith(".tif"):
        tif_files.append(os.path.join(directory, file))


for file_path in tif_files:
    file_name_stripped = os.path.splitext(os.path.basename(file_path))[0]
    new_directory = os.path.join(directory, file_name_stripped)
    catch_path = new_directory + "/catchments"
    new_directory_2 = os.path.join(new_directory,catch_path)

    print(new_directory_2)