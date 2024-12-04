import re
import re

text = 'Warsztaty jogi 2024-10-05 (id:3)'

matched_values = re.findall(r'\(id:(\d+)\)', text)[0]
print(matched_values)
