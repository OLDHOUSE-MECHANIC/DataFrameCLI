import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#So here we've defined a Function to take user input
def takeCommand():
    #It takes text input from the user and returns string output

    tc = input("Hey there! What can I do for you today? Let me know: ")

    try:
        print("Awesome! Let me process that...")
        query = tc

    except Exception as e:
        print(e)
        print("Oops, something went a little wonky. Mind giving it another shot?")
        return "None"
    return query

if __name__ == "__main__":
    df = None
    while True:
        query = takeCommand().lower()


        # If the user wants to create a pandas Series
        if 'series' in query:
            list1 = input("Got any cool values to share? Just toss 'em in, separated by a space: ")
            list1 = list1.replace(" ", ",")
            list1 = list1.split(',')
            df = pd.Series(list1)
            print("Ta-da! Here's what I whipped up:\n", df)

        # If the user wants to create a pandas DataFrame
        elif 'dataframe' in query:
            rows = input("Give me some row names, separated by commas: ")
            rows = rows.replace(" ", ",")
            rows = rows.split(',')

            columns = input("And how 'bout those column names? Type 'em on me ;) ")
            columns = columns.replace(" ", ",")
            columns = columns.split(',')

            data = {column: [] for column in columns}

            for row in rows:
                print(f"Alright, tell me values for the '{row}' row:")
                for column in columns:
                    value = input(f"{column}: ")
                    data[column].append(value)

            df = pd.DataFrame(data, index=rows)

            print("Bam! Check out this fresh DataFrame:\n", df)

        # If the user wants to modify values of the created DataFrame
        elif 'change' in query:
            row_to_modify = input("Which row needs a little twist? Tell me its name: ")
            column_to_modify = input("And which column is it? Give me the name: ")
            new_value = input("Spill the beans... what's the new value you wanna drop in? ")

            try:
                df.at[row_to_modify, column_to_modify] = new_value
                print("All set! Here's the updated DataFrame:\n", df)
            except Exception as e:
                print(e)
                print("Uh-oh, something went wrong. I'm a just a code, not a magician!")

        # If the user wants to delete a row from the DataFrame
        elif 'delete' in query and 'row' in query:
            row_to_delete = input("So what row do you want me to blow, Sargent?")

            try:
                df = df.drop(row_to_delete)
                print(f"Row '{row_to_delete}' ; Target Destroyed!.")
                print(df)
            except Exception as e:
                print(e)
                print("Uh-oh, something went wrong. I'm a just a code, not a magician!")

        # If the user wants to delete a column from the DataFrame
        elif 'delete' in query and 'column' in query:
            column_to_delete = input("Tell me, what column do you want me to Takedown?")

            try:
                df = df.drop(column_to_delete, axis=1)
                print(f"Column '{column_to_delete}' has been removed from existance.")
                print(df)
            except Exception as e:
                print(e)
                print("Uh-oh, something went wrong. Can't help ya there. Perhaps another shot Fam!")

        # If the user wants to delete a particular data point from the DataFrame
        elif 'delete' in query and 'data' in query:
            row_name = input("Enter the row name: ")
            column_name = input("Enter the column name: ")

            try:
                df.at[row_name, column_name] = None
                print(f"Data at ({row_name}, {column_name}) deleted.")
                print(df)
            except Exception as e:
                print(e)
                print("My powers feel like gone. Unable to delete data. :/ ")

        # If the user wants to add a new row to the DataFrame
        elif 'add' in query and 'row' in query:
            row_name = input("Enter the name of the new row: ")

            try:
                new_row = {column: input(f"Enter value for {column}: ") for column in df.columns}
                df.loc[row_name] = new_row
                print(f"Row '{row_name}' added.")
                print(df)
            except Exception as e:
                print(e)
                print("Error: Unable to add row.")

        # If the user wants to add a new column to the DataFrame
        elif 'add' in query and 'column' in query:
            column_name = input("Enter the name of the new column: ")

            try:
                new_column = [input(f"Enter value for {row}: ") for row in df.index]
                df[column_name] = new_column
                print(f"Column '{column_name}' added.")
                print(df)
            except Exception as e:
                print(e)
                print("Error: Unable to add column.")

        # If the user wants to visualize data using a bar graph
        elif 'graph' in query and 'bar' in query:
            df = df.apply(pd.to_numeric, errors='coerce').sum(axis=1)
            df.plot(kind='bar')
            plt.title("Bar Graph - Let's Get Graphin'!")
            plt.xlabel("X-axis")
            plt.ylabel("Y-axis")
            plt.show()

        # If the user wants to visualize data using a line graph
        elif 'graph' in query and 'line' in query:
            try:
                df.plot(kind='line')
                plt.title("Line Graph - A Dash of Data Elegance")
                plt.xlabel("X-axis")
                plt.ylabel("Y-axis")
                plt.show()
            except Exception as e:
                print(e)
                print("Uh-oh, something went wrong. I'm just a code, not a magician!")


        # If the user wants to visualize data using a graph (no specific type)
        elif 'graph' in query:
            graph_type = input("Which type of graph you wanna vibe with? (Series(Line)/Dataframe(Bar)): ")

            if 'bar' in graph_type:
                try:
                    df.plot(kind='bar')
                    plt.title("Bar Graph - Cheers to Data!")
                    plt.xlabel("X-axis")
                    plt.ylabel("Y-axis")
                    plt.show()
                except Exception as e:
                    print(e)
                    print("oops! It seems to me like you haven't made any dataframe just yet")
                    print("What are you waiting for? go get it ready fam")
            elif 'line' in graph_type:
                try:
                    df.plot(kind='line')
                    plt.title("Line Graph - A Dash of Data Elegance")
                    plt.xlabel("X-axis")
                    plt.ylabel("Y-axis")
                    plt.show()
                except Exception as e:
                    print(e)
                    print("Uh-oh, something went wrong. I'm just a code, not a magician!")
            else:
                print("Not feelin' that. Choose 'bar' or 'line', my friend!")


        elif 'add' in query:
            add_choice = input("Sure thing! You wanna add a new row or a new column? (row/column): ")

            if 'row' in add_choice:
                row_name = input("Enter the name of the new row: ")

                try:
                    new_row = {column: input(f"Enter value for {column}: ") for column in df.columns}
                    df.loc[row_name] = new_row
                    print(f"Row '{row_name}' added.")
                    print(df)
                except Exception as e:
                    print(e)
                    print("Error: Unable to add row.")

            elif 'column' in add_choice:
                column_name = input("Enter the name of the new column: ")

                try:
                    new_column = [input(f"Enter value for {row}: ") for row in df.index]
                    df[column_name] = new_column
                    print(f"Column '{column_name}' added.")
                    print(df)
                except Exception as e:
                    print(e)
                    print("Error: Unable to add column.")
            else:
                print("Sorry, I didn't quite catch that. Try 'row' or 'column'.")

        elif 'delete' in query:
            del_choice = input("Got it! Do you want to delete a row or a column? (row/column): ")

            if 'row' in del_choice:
                row_to_del = input("Which row should I wipe off the face of this DataFrame? Tell me its name: ")

                try:
                    df = df.drop(row_to_del)
                    print(f"Row '{row_to_del}' has been deleted from existence.")
                    print(df)
                except Exception as e:
                    print(e)
                    print("Oops! Something went wrong while trying to delete that row.")
            
            elif 'column' in del_choice:
                column_to_del = input("Which column should I eradicate? Gimme the name: ")

                try:
                    df = df.drop(column_to_del, axis=1)
                    print(f"Column '{column_to_del}' has been obliterated.")
                    print(df)
                except Exception as e:
                    print(e)
                    print("Oops! Something went wrong while trying to delete that column.")

            else:
                print("My apologies, I couldn't quite catch that. Try 'row' or 'column'.")

        elif 'save' in query:
            if df is None:
                print("Nothing to save! You need to create a DataFrame first.")
            else:
                file_name = input("Enter the name of the file (without extension) to save: ")
                try:
                    df.to_csv(f"{file_name}.csv",)
                    print(f"DataFrame saved as {file_name}.csv")
                except Exception as e:
                    print(e)
                    print("Oops! Something went wrong while saving the DataFrame.")

        elif 'load' in query:
            file_name = input("Enter the name of the file (without extension) to load: ")
            try:
                df = pd.read_csv(f"{file_name}.csv")
                print(f"DataFrame loaded from {file_name}.csv")
            except Exception as e:
                print(e)
                print("Oops! Something went wrong while loading the DataFrame.")
        
        elif 'show' in query:
            show_choice = input("Sure thing! Would you like to see a graph or a table? (graph/table): ")

            if 'graph' in show_choice:
                graph_type = input("Which type of graph you wanna vibe with? (bar/line): ")

                if 'bar' in graph_type:
                    try:
                        df.plot(kind='bar')
                        plt.title("Bar Graph - Cheers to Data!")
                        plt.xlabel("X-axis")
                        plt.ylabel("Y-axis")
                        plt.show()
                    except Exception as e:
                        print(e)
                        print("Oops! It seems you haven't created a DataFrame yet. Get ready to roll with some data!")
                
                elif 'line' in graph_type:
                    try:
                        df.plot(kind='line')
                        plt.title("Line Graph - A Dash of Data Elegance")
                        plt.xlabel("X-axis")
                        plt.ylabel("Y-axis")
                        plt.show()
                    except Exception as e:
                        print(e)
                        print("Uh-oh, something went wrong. I'm just a code, not a magician!")

                else:
                    print("Not feelin' that. Choose 'bar' or 'line', my friend!")

            elif 'table' in show_choice:
                if df is None:
                    print("There's no DataFrame to show. Create one first!")
                else:
                    print("Here's the DataFrame:")
                    print(df)

            else:
                print("I'm a bit puzzled. Would you like to see a 'graph' or a 'table'?")

        elif 'quit' in query or 'bye' in query or 'shutdown' in query or 'close' in query:
            print(Turning off the program...)
            quit()
            
