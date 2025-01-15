import pandas as pd
import string
import sqlite3

class CreateKaggleSurveyDB:
    def __init__(self):
        survey_years = [2020, 2021, 2022]
        df_dict = dict()
        for survey_year in survey_years:
            file_path = f"data/kaggle_survey_{survey_year}_responses.csv"
            df = pd.read_csv(file_path, low_memory=False, skiprows=[1])
            df = df.iloc[:, 1:]
            df_dict[survey_year, "responses"] = df
            df = pd.read_csv(file_path, nrows=1)
            question_descriptions = df.values.ravel()
            question_descriptions = question_descriptions[1:]
            df_dict[survey_year, "question_descriptions"] = question_descriptions
        self.survey_years = survey_years
        self.df_dict = df_dict

    def tidy_2020_2021_data(self, survey_year: int) -> tuple:
        question_indexes, question_types, question_descriptions = [], [], []
        column_names = self.df_dict[survey_year, "responses"].columns
        descriptions = self.df_dict[survey_year, "question_descriptions"]
        for column_name, question_description in zip(column_names, descriptions):
            column_name_split = column_name.split("_")
            question_description_split = question_description.split(" - ")
            if len(column_name_split) == 1:
                question_index = column_name_split[0]
                question_indexes.append(question_index)
                question_types.append("Multiple choice")
                question_descriptions.append(question_description_split[0])
            else:
                if column_name_split[1] in string.ascii_uppercase:
                    question_index = column_name_split[0] + column_name_split[1]
                    question_indexes.append(question_index)
                else:
                    question_index = column_name_split[0]
                    question_indexes.append(question_index)
                question_types.append("Multiple selection")
                question_descriptions.append(question_description_split[0])
        question_df = pd.DataFrame()
        question_df["question_index"] = question_indexes
        question_df["question_type"] = question_types
        question_df["question_description"] = question_descriptions
        question_df["surveyed_in"] = survey_year
        question_df = question_df.groupby(["question_index", "question_type", "question_description", "surveyed_in"]).count().reset_index()
        response_df = self.df_dict[survey_year, "responses"]
        response_df.columns = question_indexes
        response_df_reset_index = response_df.reset_index()
        response_df_melted = pd.melt(response_df_reset_index, id_vars="index", var_name="question_index", value_name="response")
        response_df_melted["responded_in"] = survey_year
        response_df_melted = response_df_melted.rename(columns={"index": "respondent_id"})
        response_df_melted = response_df_melted.dropna().reset_index(drop=True)
        return question_df, response_df_melted

    def tidy_2022_data(self, survey_year: int) -> tuple:
        question_indexes, question_types, question_descriptions = [], [], []
        column_names = self.df_dict[survey_year, "responses"].columns
        descriptions = self.df_dict[survey_year, "question_descriptions"]
        for column_name, question_description in zip(column_names, descriptions):
            column_name_split = column_name.split("_")
            question_description_split = question_description.split(" - ")
            if len(column_name_split) == 1:
                question_types.append("Multiple choice")
            else:
                question_types.append("Multiple selection")
            question_index = column_name_split[0]
            question_indexes.append(question_index)
            question_descriptions.append(question_description_split[0])
        question_df = pd.DataFrame()
        question_df["question_index"] = question_indexes
        question_df["question_type"] = question_types
        question_df["question_description"] = question_descriptions
        question_df["surveyed_in"] = survey_year
        question_df = question_df.groupby(["question_index", "question_type", "question_description", "surveyed_in"]).count().reset_index()
        response_df = self.df_dict[survey_year, "responses"]
        response_df.columns = question_indexes
        response_df_reset_index = response_df.reset_index()
        response_df_melted = pd.melt(response_df_reset_index, id_vars="index", var_name="question_index", value_name="response")
        response_df_melted["responded_in"] = survey_year
        response_df_melted = response_df_melted.rename(columns={"index": "respondent_id"})
        response_df_melted = response_df_melted.dropna().reset_index(drop=True)
        return question_df, response_df_melted

    def create_database(self):
        question_df = pd.DataFrame()
        response_df = pd.DataFrame()
        for survey_year in self.survey_years:
            if survey_year == 2022:
                q_df, r_df = self.tidy_2022_data(survey_year)
            else:
                q_df, r_df = self.tidy_2020_2021_data(survey_year)
            question_df = pd.concat([question_df, q_df], ignore_index=True)
            response_df = pd.concat([response_df, r_df], ignore_index=True)
        connection = sqlite3.connect("data/kaggle_survey.db")
        question_df.to_sql("questions", con=connection, if_exists="replace", index=False)
        response_df.to_sql("responses", con=connection, if_exists="replace", index=False)
        cur = connection.cursor()
        drop_view_sql = """DROP VIEW IF EXISTS aggregated_responses;"""
        create_view_sql = """
        CREATE VIEW aggregated_responses AS
        SELECT questions.surveyed_in,
               questions.question_index,
               questions.question_type,
               questions.question_description,
               responses.response,
               COUNT(responses.respondent_id) AS response_count
          FROM questions
          JOIN responses
            ON responses.question_index = questions.question_index AND
               responses.responded_in = questions.surveyed_in
         GROUP BY questions.surveyed_in,
                  questions.question_index,
                  responses.response;
        """
        cur.execute(drop_view_sql)
        cur.execute(create_view_sql)
        connection.close()

create_kaggle_survey_db = CreateKaggleSurveyDB()
create_kaggle_survey_db.create_database()

"""
# Read csv files
survey_years = [2020, 2021, 2022]
df_dict = dict()
for survey_year in survey_years:
    file_path = f"data/kaggle_survey_{survey_year}_responses.csv"
    df = pd.read_csv(file_path, low_memory=False, skiprows=[1])
    df = df.iloc[:, 1:] # Skipp survey time
    df_dict[survey_year, "responses"] = df
    df = pd.read_csv(file_path, nrows=1)
    question_descriptions = df.values.ravel()
    question_descriptions = question_descriptions[1:]
    df_dict[survey_year, "question_descriptions"] = question_descriptions

df_dict[2020, "question_descriptions"]
df_dict[2020, "responses"].head()
df_dict[2021, "question_descriptions"]
df_dict[2021, "responses"].head()
df_dict[2022, "question_descriptions"]
df_dict[2022, "responses"]

# Organize data in 2020/2021
survey_year = 2020
question_indexes, question_types, question_descriptions = [], [], []
column_names = df_dict[survey_year, "responses"].columns
descriptions = df_dict[survey_year, "question_descriptions"]
for column_name, question_description in zip(column_names, descriptions):
    column_name_split = column_name.split("_")
    question_description_split = question_description.split(" - ")
    if len(column_name_split) == 1:
        question_index = column_name_split[0]
        question_indexes.append(question_index)
        question_types.append("Multiple choice")
        question_descriptions.append(question_description_split[0])
    else:
        if column_name_split[1] in string.ascii_uppercase:
            question_index = column_name_split[0] + column_name_split[1]
            question_indexes.append(question_index)
        else:
            question_index = column_name_split[0]
            question_indexes.append(question_index)
        question_types.append("Multiple selection")
        question_descriptions.append(question_description_split[0])

question_df = pd.DataFrame()
question_df["question_index"] = question_indexes
question_df["question_type"] = question_types
question_df["question_description"] = question_descriptions
question_df["surveyed_in"] = survey_year
question_df = question_df.groupby(["question_index", "question_type", "question_description", "surveyed_in"]).count().reset_index()
question_df.head()

response_df = df_dict[survey_year, "responses"]
response_df.columns = question_indexes
response_df_reset_index = response_df.reset_index()
response_df_melted = pd.melt(response_df_reset_index, id_vars="index", var_name="question_index", value_name="response")
response_df_melted["responded_in"] = survey_year
response_df_melted = response_df_melted.rename(columns={"index": "respondent_id"})
response_df_melted = response_df_melted.dropna().reset_index(drop=True)
response_df_melted

# Organize data in 2022
survey_year = 2022
question_indexes, question_types, question_descriptions = [], [], []
column_names = df_dict[survey_year, "responses"].columns
descriptions = df_dict[survey_year, "question_descriptions"]
for column_name, question_description in zip(column_names, descriptions):
    column_name_split = column_name.split("_")
    question_description_split = question_description.split(" - ")
    if len(column_name_split) == 1:
        question_types.append("Multiple choice")
    else:
        question_types.append("Multiple selection")
    question_index = column_name_split[0]
    question_indexes.append(question_index)
    question_descriptions.append(question_description_split[0])

question_df = pd.DataFrame()
question_df["question_index"] = question_indexes
question_df["question_type"] = question_types
question_df["question_description"] = question_descriptions
question_df["surveyed_in"] = survey_year
question_df = question_df.groupby(["question_index", "question_type", "question_description", "surveyed_in"]).count().reset_index()
question_df.head()

response_df = df_dict[survey_year, "responses"]
response_df.columns = question_indexes
response_df_reset_index = response_df.reset_index()
response_df_melted = pd.melt(response_df_reset_index, id_vars="index", var_name="question_index", value_name="response")
response_df_melted["responded_in"] = survey_yeardata_year
response_df_melted = response_df_melted.rename(columns={"index": "respondent_id"})
response_df_melted = response_df_melted.dropna().reset_index(drop=True)
response_df_melted

"""