import time
start_time = time.time()
import os
import math
import shutil

### SPIRAL ##########################################################################################
def convert_svg_to_gcode(file_name):
    # Öffne die SVG-Datei zum Lesen
    with open(file_name, 'r') as svg_file:
        # Lies die Zeilen der Datei
        lines = svg_file.readlines()

    # Lösche die ersten 4 Zeilen
    del lines[:4]
    # Lösche die letzte Zeile
    del lines[len(lines)-1]

    # Entferne Zeilen 
    lines = [line for line in lines if "<!-- Mask -->" not in line]
    lines = [line for line in lines if "<!-- Out of bounds -->" not in line]
    lines = [line for line in lines if "<!-- Maximum Shape Length -->" not in line]

    # Füge die ersten beiden Zeilen ein
    lines.insert(0, "G90\n")  # Füge "G90" als erste Zeile ein
    lines.insert(1, lines[1])   # Einfügen der ersten Gcode Zeile als Startwert (G92 wird später eingefügt) vom Bild
    lines.insert(2, 'G1 F' + str(feedrate) + '\n')  # Füge Gesamtfeedrate ein

    # Ersetze Leerzeichen und Kommas entsprechend den Anforderungen
    for i in range(len(lines)):
        # Ersetze 4 Leerzeichen mit "G1 X"
        lines[i] = lines[i].replace("    ", "G1 X")
        # Ersetze Kommas mit " Y"
        lines[i] = lines[i].replace(",", " Y")
        # Ersetze "  "/>" mit "M280"
        lines[i] = lines[i].replace('  " />', "M280")
        # Ersetze "<polyline fill="none" stroke="#000000" points="" mit der übernächsten zeile
        lines[i] = lines[i].replace('  <polyline fill="none" stroke="#000000" points="', "M280")
            
    for i in range(len(lines) - 2):  # Iterate until the second last line
        if lines[i].strip() == "M280" and lines[i+1].strip() == "M280":  # Check if two consecutive lines are "M280"
            lines[i+1], lines[i+2] = lines[i+2], lines[i+1]  # Swap the next line with the second "M280"

    lines[1] = lines[1].replace("G1", "G92")  # Erste Gcode Zeile als Startwert (aktuelle position - G92) setzen 

    # Speichere die neuen Zeilen in spiral_gcode.txt
    with open('./output/auxilary/spiral_gcode.txt', 'w') as gcode_file:
        gcode_file.writelines(lines)

    if debug:
        print(" >>> Spiral_gcode.txt")


### SCALE and Home ##########################################################################################
def scale_gcode_auto(input_file_gcode, output_file_scaled, XMax, YMax):
    with open(input_file_gcode, 'r') as f_in:       # max/min values search
        x_values = []
        y_values = []
        for line in f_in:
            if line.startswith('G0') or line.startswith('G1') or line.startswith('G92'):
                values = line.split()
                for value in values:
                    if value.startswith('X'):
                        x_values.append(float(value[1:]))      
                    elif value.startswith('Y'):
                        y_values.append(float(value[1:]))     


    # Calculate scale factor
    max_x = max(x_values)
    min_x = min(x_values)
    max_y = max(y_values)
    min_y = min(y_values)
    scale_factor = max(abs(max_x - min_x), abs(max_y - min_y)) / max(XMax, YMax)

    # Debug mode
    if debug:
        print(" > Scalefaktor:", scale_factor)
        print("min_x:", min_x, " --> ", min_x/scale_factor)
        print("max_x:", max_x, " --> ", max_x/scale_factor)
        print("min_y:", min_y, " --> ", min_y/scale_factor)
        print("max_y:", max_y, " --> ", max_y/scale_factor)
    
    max_x = max_x/scale_factor
    min_x = min_x/scale_factor
    max_y = max_y/scale_factor
    min_y = min_y/scale_factor

    with open(input_file_gcode, 'r') as f_in, open(output_file_scaled, 'w') as f_out:
        for line in f_in:
            if line.startswith('G0') or line.startswith('G1') or line.startswith('G92'):
                scaled_values = []
                values = line.split()
                for value in values:
                    if value.startswith('X'):
                        x_value = float(value[1:]) / scale_factor
                        scaled_values.append('X' + str(x_value))
                    elif value.startswith('Y'):
                        y_value = float(value[1:]) / scale_factor
                        scaled_values.append('Y' + str(y_value))
                    else:
                        scaled_values.append(value)
                f_out.write(' '.join(scaled_values) + '\n')
            else:
                f_out.write(line)
    if debug:
        print(" >>> scaled_gcode.txt")
        print(" > Homing (Start at Penpoint)")
        print("start_x:", x_values[0], " --> ", 0)
        print("start_y:", y_values[0], " --> ", 0)

    # Homing: Startposition wird dem ganzen Gcode abgezogen
    for i in range(len(x_values)):    
        x_values[i] = x_values[i] - x_values[0] 
    for i in range(len(y_values)):    
        y_values[i] = y_values[i] - y_values[0] 

    # Insert Outline of image
    with open(output_file_scaled, 'r') as outline_file:
        lines = outline_file.readlines()
        lines.insert(3, 'G1 X'+ str(min_x) + ' Y' + str(min_y) + '\n') 
        lines.insert(4, 'G1 X'+ str(min_x) + ' Y' + str(max_y) + '\n') 
        lines.insert(5, 'G1 X'+ str(max_x) + ' Y' + str(max_y) + '\n') 
        lines.insert(6, 'G1 X'+ str(max_x) + ' Y' + str(min_y) + '\n') 
        lines.insert(7, 'G1 X'+ str(min_x) + ' Y' + str(min_y) + '\n') 
        lines.insert(9, 'M280\n')     
        # Speichere die neuen Zeilen in spiral_gcode.txt
    with open(output_file_scaled, 'w') as output_file:
        output_file.writelines(lines)
    if debug:
        print(" >> Outline")
        print(" >>> spiral_gcode.txt")



### ROUND ##########################################################################################
def round_gcode(output_file_scaled, output_file_rounded):
    with open(output_file_scaled, 'r') as f_in, open(output_file_rounded, 'w') as f_out:
        for line in f_in:
            if line.startswith('G0') or line.startswith('G1') or line.startswith('G92'):
                rounded_values = []
                values = line.split()
                for value in values:
                    if value.startswith('X') or value.startswith('Y'):
                        # Parse the numerical value
                        num_value = float(value[1:])
                        # Round to three decimal places using multiples of 0.016
                        rounded_value = round(num_value / 0.016) * 0.016
                        # Format the rounded value with three decimal places
                        formatted_value = '{:.3f}'.format(rounded_value)
                        # Append the rounded value to the list
                        rounded_values.append(value[0] + formatted_value)
                    else:
                        rounded_values.append(value)
                # Write the rounded values to the output file
                f_out.write(' '.join(rounded_values) + '\n')
            else:
                # If the line doesn't start with 'G1', write it unchanged to the output file
                f_out.write(line)
        if debug:
            print(" >>> rounded_gcode.txt")



### Find min Dfference between to points
def find_min_difference(filename):
    """Find the smallest difference between x and y coordinates in the file."""
    with open(filename, 'r') as file:
        lines = file.readlines()
        x_values = []
        y_values = []
        differences_x = []
        differences_y = []

        for line in lines:
            if line.startswith('G1'):
                parts = line.split(' ')
                x_index = next((i for i, part in enumerate(parts) if 'X' in part), None)
                y_index = next((i for i, part in enumerate(parts) if 'Y' in part), None)
                if x_index is not None and y_index is not None:
                    try:
                        x = float(parts[x_index].split('X')[1])
                        y = float(parts[y_index].split('Y')[1])
                        x_values.append(x)
                        y_values.append(y)
                    except (IndexError, ValueError):
                        pass

        for i in range(len(x_values) - 1):
            diff_x = abs(x_values[i+1] - x_values[i])
            diff_y = abs(y_values[i+1] - y_values[i])
            if diff_x != 0:  
                differences_x.append(diff_x)
            if diff_y != 0:  
                differences_y.append(diff_y)

        min_diff_x = min(differences_x) if differences_x else 0  
        min_diff_y = min(differences_y) if differences_y else 0  

        return min_diff_x, min_diff_y
    

# Veränderbare Variablen
feedrate = 13      #[mm]
outputsize_max_mm_HxB_Image = 100   #Breite und Höhe des Bildes [mm]

#Debugmodus?
debug = True

# Dateinamen der In- und Outputfiles
input_file_svg = './SVG.svg'
output_file_gcode = './gcode.txt'

# Relativ-Pfade für neue Output-Ordner angeben
output_path = "./output"
output_aux_path = "./output/auxilary"

# Überprüfen, und Ordner erstellen
if os.path.exists(output_path):
    pass
else:
    os.mkdir(output_path)
if os.path.exists(output_aux_path):
    pass
else:
    os.mkdir(output_aux_path)

XMax = outputsize_max_mm_HxB_Image
YMax = outputsize_max_mm_HxB_Image

# Funktionsaufrufe
convert_svg_to_gcode(input_file_svg)
scale_gcode_auto(output_aux_path + '/spiral_gcode.txt', output_aux_path + '/scaled_gcode.txt', XMax, YMax)
round_gcode(output_aux_path + '/scaled_gcode.txt', output_aux_path + '/rounde_gcode.txt')

from fx_trans import fxtrans_gcode
fxtrans_gcode(input_file= output_aux_path + '/rounded_gcode.txt', 
              output_file= output_aux_path + '/transformed_gcode.txt', 
              B=795., x0=474-85, y0=535)

if debug:
    min_diff_x_befor, min_diff_y_befor = find_min_difference(output_aux_path + '/spiral_gcode.txt')
    min_diff_x_after, min_diff_y_after = find_min_difference(output_file_gcode)
    print(" > Kleinste Differenz vorher  -->  nachher (0,016mm)")
    print("min_x:", min_diff_x_befor, " --> ", min_diff_x_after)
    print("min_y:", min_diff_y_befor, " --> ", min_diff_y_after)

# Datei kopieren und umbenennen
shutil.copyfile(output_aux_path + '/transformed_gcode.txt', output_path + '/gcode.txt')
shutil.copyfile('SVG.svg', output_path + '/SVG.svg')
shutil.copyfile(output_path + '/gcode.txt', 'gcode.txt')

# Prüfen, ob die Datei erfolgreich kopiert und umbenannt wurde
if os.path.exists('gcode.txt'):
    if debug:
        print("")
        print(" >>> Voilá-, itsefinisch <<< ")
        print("")
else:
    print(" -|- AAAgrat itseKAPUT -|- ")

end_time = time.time()
execution_time = end_time - start_time
print(" > Konvertierzeit:  ", execution_time, "  Sekunden")