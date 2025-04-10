import os
import subprocess
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        db_type = request.form["db_type"]
        host = request.form["host"]
        user = request.form["user"]
        password = request.form["password"]
        database = request.form["database"]
        table_select = request.form["table_select"]
        table_name = request.form.get("table_name")
        backup_folder = request.form["backup_folder"]

        # Validate folder path
        if not os.path.exists(backup_folder):
            return jsonify({"error": "The specified backup folder does not exist!"})

        # Get current timestamp for backup file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{database}_{timestamp}.bak"
        backup_filepath = os.path.join(backup_folder, backup_filename)

        if db_type == "mysql":
            # MySQL: Use mysqldump to create a .sql file
            command = [
                "mysqldump",
                "-h", host,
                "-u", user,
                f"-p{password}",
                database,
                table_name if table_select == "specific" else ""
            ]
            try:
                with open(backup_filepath, "w") as backup_file:
                    subprocess.run(command, stdout=backup_file, check=True)
                return jsonify({"success": f"Backup successful! Saved to {backup_filepath}"})
            except subprocess.CalledProcessError:
                return jsonify({"error": "Error creating backup for MySQL."})

        elif db_type == "mssql":
            if table_select == "all":
                # MSSQL: Backup entire database as .bak file
                command = [
                    "sqlcmd",
                    "-S", host,
                    "-U", user,
                    "-P", password,
                    "-Q", f"BACKUP DATABASE {database} TO DISK = '{backup_filepath}'"
                ]
                try:
                    subprocess.run(command, check=True)
                    return jsonify({"success": f"Backup successful! Saved to {backup_filepath}"})
                except subprocess.CalledProcessError:
                    return jsonify({"error": "Error creating backup for MSSQL database."})
            else:
                # MSSQL: Backup specific table(s) using BCP or export (not directly to .bak)
                tables = [table.strip() for table in table_name.split(",")]
                for table in tables:
                    # Export specific tables to a .sql or .csv file (not .bak)
                    table_backup_filepath = os.path.join(backup_folder, f"{table}_{timestamp}.sql")
                    command = [
                        "sqlcmd",
                        "-S", host,
                        "-U", user,
                        "-P", password,
                        "-Q", f"SELECT * FROM {database}.dbo.{table} INTO OUTFILE '{table_backup_filepath}'"
                    ]
                    try:
                        subprocess.run(command, check=True)
                    except subprocess.CalledProcessError:
                        return jsonify({"error": f"Error creating backup for MSSQL table {table}."})

                return jsonify({"success": "Backup successful for specified tables."})

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
