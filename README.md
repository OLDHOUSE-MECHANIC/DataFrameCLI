# DataFrameCLI

This project started as a simple experiment to make working with Pandas a little less intimidating and a lot more interactive.

**DataFrameCLI** is a Python-based command-line tool that lets you create, modify, explore, and visualize Pandas DataFrames through plain-text commands. Instead of writing Pandas code for every small task, you can talk to the program and it does hard work.
pretty cool, right?

---

## What can it do?

Once the program is running, you can:

* Create Pandas **Series** and **DataFrames** from scratch
* Add, edit, or delete rows and columns
* Change individual data values
* Visualize your data using:

  * Bar charts
  * Line graphs
* Save your DataFrame as a CSV file
* Load an existing CSV file back into the program
* View your data as a table or graph at any time

Everything happens interactively through the terminal, with prompts guiding you along the way.

---

## Why this project exists

When learning Pandas, a lot of beginners struggle with:

* Remembering syntax
* Understanding how DataFrames actually change
* Quickly visualizing what their data looks like

This project was built to solve exactly that. It turns common Pandas operations into a conversational CLI experience, making it easier to experiment, make mistakes, and learn by doing.

---

## Tech stack

* **Python**
* **Pandas** for data handling
* **NumPy** for numerical operations
* **Matplotlib** for data visualization

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/OLDHOUSE-MECHANIC/DataFrameCLI.git
cd DataFrameCLI
pip install -r requirements.txt
```

---

## Running the program

Start the application with:

```bash
python main.py
```

You’ll be greeted with a prompt asking what you’d like to do. From there, you can type things like:

* `create dataframe`
* `add row`
* `delete column`
* `show graph`
* `save`
* `load`
* `quit`

The program will ask follow-up questions whenever it needs more information.

---

## Example use case

You might start by creating a DataFrame, add some rows of data, tweak a few values, visualize the result as a bar chart, and then save it to a CSV — all without writing a single Pandas command yourself.

---

## Current limitations

This is an early-stage project and intentionally kept simple. Some things that could be improved:

* Better input validation
* Cleaner command parsing
* More visualization options
* Modularizing the codebase
* Adding tests

---

## License

This project is open-source and released under the MIT License.

Feel free to explore, modify, and build on top of it.
