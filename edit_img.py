import csv


def get_level(level_number):
    with open(f"data/level{level_number}.csv", mode="r", encoding="utf-8") as csv_file:
        level = list(csv.reader(csv_file, delimiter=",", quotechar="\""))
    return level


level_map = get_level(1)
for i in range(len(level_map)):
    for j in range(len(level_map[0])):
        if level_map[i][j] == "2":
            level_map[i][j] = "1"

with open(f"data/level1.csv", mode="w", encoding="utf-8", newline="") as csv_file:
    writer = csv.writer(csv_file, delimiter=",", quotechar="\"", quoting=csv.QUOTE_MINIMAL)
    for row in level_map:
        print(row)
        writer.writerow(row)
