import timetable
import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Timetable")
root.iconbitmap("src/icon.ico")
root.geometry("1600x800")
root.resizable(False, False)

week = timetable.get_timetable()

table = ttk.Treeview(root, columns=("Monday", "Tuesday", "Wednesday", "Thursday", "Friday"))

table.column("#0", width=100,  stretch="NO")

for column in table["columns"]:
    table.heading(column, text=column)
    table.column(column, width=300, stretch="NO")
    rows = ()
    # TODO: add a loop to add the rows
    for i, j in zip(week, ) #???
    table.insert("", "end", column, text="", values=("", "", "", "", "")) # <---

table.pack()
root.mainloop()