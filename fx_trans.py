import math


def scale_gcode_auto(input_file, output_file, XMax, YMax, debug=False):
    with open(input_file, 'r') as f_in:
        x_values = []
        y_values = []
        for line in f_in:
            if line.startswith('G1') or line.startswith('G0'):
                values = line.split()
                for value in values:
                    if value.startswith('X'):
                        x_values.append(float(value[1:]))
                    elif value.startswith('Y'):
                        y_values.append(float(value[1:]))

    # Calculate scale factor
    max_x = max(x_values)
    min_x = min(x_values)qfqefqe
    max_y = max(y_values)
    min_y = min(y_values)
    scale_factor = max(abs(max_x) - abs(min_x), abs(max_y) - abs(min_y)) / max(XMax, YMax)
    scale_factor = max(max_x-min_x, max_y-min_y) / max(XMax, YMax)

    # Debug mode
    if debug:
        print("min_x:", min_x)
        print("max_x:", max_x)
        print("min_y:", min_y)
        print("max_y:", max_y)
        print("scale_factor:", scale_factor)

    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            if line.startswith('G1') or line.startswith('G0'):
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


def round_gcode(input_file, output_file):
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            if line.startswith('G1') or line.startswith('G0'):
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


def set_centerposition(filename):
    # 1. Datei öffnen und den gesamten Inhalt lesen
    with open(filename, 'r') as file:
        content = file.read()

    # 2. Das erste Vorkommen von "G1" durch "G92" ersetzen
    replaced_content = content.replace('G1', 'G92', 1)

    # 3. Die modifizierte Inhalte zurück in die Datei schreiben
    with open(filename, 'w') as file:
        file.write(replaced_content)



def fxtrans_gcode(input_file, output_file, B=810., x0=None, y0=None):
    if x0 is None:
        x0 = B / 2
    if y0 is None:
        y0 = B / 2

    def l1(x, y):
        y=-y            #Entspiegeln der y-Achse
        l1q = (x0+x)**2 + (y0+y)**2
        return math.sqrt(l1q)
    def l2(x, y):
        y=-y            #Entspiegeln der y-Achse
        l2q = (B-x0-x)**2 + (y0+y)**2
        return math.sqrt(l2q)

    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        x, y = 0, 0
        for line in f_in:
            if line.startswith('G0') or line.startswith('G1'):
                trans_val = []
                values = line.split()
                for value in values:
                    if value.startswith('X'):
                        x = float(value[1:])
                    elif value.startswith('Y'):
                        y = float(value[1:])
                line = f"G0 X{l1(x, y)} Y{l2(x, y)}\n"
            f_out.write(line)

def main():
    input_file = 'gcode.txt'
    scaled_file = 'scaled_gcode.txt'
    output_file = 'pure_gcode.txt'
    trans_file = "trans_gcode.txt"
    trans_file_raw = "trans_raw_gcode.txt"
    outputsize_max_mm_HxB_Image = 200   #Breite und Höhe der output SVG
    XMax = outputsize_max_mm_HxB_Image  # Example maximum X value
    YMax = outputsize_max_mm_HxB_Image  # Example maximum Y value

    scale_gcode_auto(input_file, scaled_file, XMax, YMax, debug=True)
    round_gcode(scaled_file, output_file)
    set_centerposition(input_file)
    set_centerposition(output_file)
    fxtrans_gcode(input_file=output_file, output_file=trans_file_raw)
    
    #set_centerposition(trans_file_raw)
    round_gcode(trans_file_raw, trans_file)


if __name__ == "__main__":
    main()

    