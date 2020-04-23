"""Web interface"""
from typing import List, Tuple

import altair as alt
import pandas as pd
import streamlit as st
from textblob import TextBlob

import src.analyzer as az
import src.doc_similarity as ds
import src.markdown as md
import src.summarizer as sz
import src.topic_modeling as tm


# resources/cs100f2019_lab05_reflections


def main():
    """main streamlit function"""
    # Title
    st.sidebar.title("What to do")
    global directory
    global main_df
    directory = st.sidebar.text_input("Path to directory")
    if directory != "":
        try:
            main_df = df_preprocess(directory)
            st.sidebar.success(f"Analyzing {directory} ....")
        except FileNotFoundError as err:
            st.sidebar.text(err)
    analysis_mode = st.sidebar.selectbox(
        "Choose the analysis mode",
        [
            "Home",
            "Frequency Analysis",
            "Sentiment Analysis",
            "Summary",
            "Topic Modeling",
            "Document Similarity",
        ],
    )
    if analysis_mode == "Home":
        with open("README.md") as readme_file:
            st.markdown(readme_file.read())
    if analysis_mode == "Frequency Analysis":
        st.title("Frequency Analysis")
        frequency()
    elif analysis_mode == "Sentiment Analysis":
        st.title("Sentiment Analysis")
        sentiment()
    elif analysis_mode == "Summary":
        st.title("Summary")
        summary()
    elif analysis_mode == "Topic Modeling":
        st.title("Topic Modeling")
        tpmodel()
    elif analysis_mode == "Document Similarity":
        st.title("Document Similarity")
        doc_sim()


def df_preprocess(directory_path):
    "build and preprocess pandas dataframe"
    raw_df = pd.DataFrame(md.collect_md(directory_path))
    df_combined = combine_column_text(raw_df)
    return df_combined


def combine_column_text(raw_df):
    """Combined the questions and store into a new column"""
    df_combined = raw_df
    # filter out first column -- user info
    cols = df_combined.columns[1:]
    # combining text into combined column
    df_combined["combined"] = df_combined[cols].apply(
        lambda row: " ".join(row.values.astype(str)), axis=1
    )

    return df_combined


def frequency():
    """main function for frequency analysis"""
    freq_type = st.sidebar.selectbox(
        "Type of frequency analysis", ["Overall", "Student", "Question"]
    )
    freq_range = st.sidebar.slider(
        "Select a range of Most frequent words", 1, 50, value=25
    )
    if freq_type == "Overall":
        st.sidebar.success(
            'To continue see individual frequency analysis select "Individual"'
        )
        st.header("Overall most frequent words in the directory")
        overall_freq(freq_range)
    elif freq_type == "Student":
        st.header("Most frequent words by individual students")
        individual_student_freq(main_df, freq_range)
    elif freq_type == "Question":
        st.header("Most frequent words in individual questions")
        individual_question_freq(main_df, freq_range)


def sentiment():
    """main function for sentiment analysis"""
    # calculate overall sentiment from the combined text
    main_df["sentiment"] = main_df["combined"].apply(
        lambda x: TextBlob(x).sentiment.polarity
    )
    senti_type = st.sidebar.selectbox(
        "Type of sentiment analysis", ["Overall", "Student", "Question"]
    )
    if senti_type == "Overall":
        st.sidebar.success(
            'To continue see individual sentiment analysis select "Individual"'
        )
        st.header("Overall sentiment polarity in the directory")
        overall_senti(main_df)
    elif senti_type == "Student":
        st.header("View sentiment by individual students")
        individual_student_senti(main_df)
    elif senti_type == "Question":
        st.header("View sentiment by individual questions")
        individual_question_senti(main_df)


def summary():
    """Display summarization"""
    summary_df = pd.DataFrame(sz.summarizer(directory))
    st.write(summary_df)


def tpmodel():
    """Display topic modeling"""
    topic_range = st.sidebar.slider(
        "Select the amount of topics", 1, 10, value=5
    )
    word_range = st.sidebar.slider(
        "Select the amount of words per topic", 1, 10, value=5
    )
    main_df["topics"] = main_df["combined"].apply(
        lambda x: tm.topic_model(
            x, NUM_TOPICS=topic_range, NUM_WORDS=word_range
        )
    )
    st.write(main_df)


def doc_sim():
    """Display document similarity"""
    st.header("Similarity between each student's document")
    main_df["normal_text"] = main_df["combined"].apply(
        lambda x: az.normalize(x)
    )
    pairs = ds.create_pair(main_df["Reflection by"])
    # calculate similarity of the docs of the selected author pairs
    similarity = [
        ds.tfidf_cosine_similarity(
            (
                main_df[main_df["Reflection by"] == pair[0]][
                    "normal_text"].values[0],
                main_df[main_df["Reflection by"] == pair[1]][
                    "normal_text"].values[0],
            )
        )
        for pair in pairs
    ]
    df_sim = pd.DataFrame({"pair": pairs, "similarity": similarity})
    # Split the pair tuple into two columns for plotting
    df_sim[['doc_1', 'doc_2']] = pd.DataFrame(
        df_sim['pair'].tolist(), index=df_sim.index
    )
    # st.write(df_sim)
    heatmap = alt.Chart(df_sim).mark_rect().encode(
        x=alt.X('doc_1', sort=None, title="student"),
        y=alt.Y('doc_2', sort="-x", title="student"),
        color='similarity',
        tooltip=[
            alt.Tooltip("similarity", title="similarity"),
        ]
    )
    st.altair_chart(heatmap)


def overall_freq(freq_range):
    """page fore overall word frequency"""
    plot_frequency(az.dir_frequency(directory, freq_range))


def overall_senti(senti_df):
    """page for overall senti"""
    plot_overall_senti(senti_df)


def plot_overall_senti(senti_df):
    """Visulize overall sentiment with histogram and scatter plots"""
    senti_hist = (
        alt.Chart(senti_df)
        .mark_bar()
        .encode(
            alt.X("sentiment", bin=True),
            y="count()",
            opacity=alt.value(0.7),
            color=alt.value("blue"),
        )
    )
    senti_point = (
        alt.Chart(senti_df)
        .mark_point()
        .encode(
            x="Reflection by",
            y="sentiment",
            color="Reflection by",
            tooltip=[
                alt.Tooltip("sentiment", title="polarity"),
                alt.Tooltip("Reflection by", title="author"),
            ],
        )
    )

    st.altair_chart(senti_hist)
    st.altair_chart(senti_point)


def individual_student_senti(input_df):
    """page for display individual student's sentiment"""
    students = st.multiselect(
        label="Select specific students below:",
        options=input_df["Reflection by"]
    )
    df_selected_stu = input_df.loc[input_df["Reflection by"].isin(students)]
    senti_df = pd.DataFrame(
        df_selected_stu, columns=["Reflection by", "sentiment"]
    )
    if len(students) != 0:
        plot_student_sentiment(senti_df)


def individual_question_senti(input_df):
    """page for individual question's sentiment"""
    st.write(input_df)
    questions = st.multiselect(
        label="Select specific questions below:", options=input_df.columns[1:]
    )
    select_text = []
    for column in questions:
        select_text.append(input_df[column].to_string(index=False))
    questions_senti_df = pd.DataFrame(
        {"questions": questions, "text": select_text}
    )
    # calculate overall sentiment from the combined text
    questions_senti_df["sentiment"] = questions_senti_df["text"].apply(
        lambda x: TextBlob(x).sentiment.polarity
    )
    if len(select_text) != 0:
        plot_question_sentiment(questions_senti_df)


def plot_student_sentiment(senti_df):
    """plot sentiment by student from a df containing name and senti"""
    senti_plot = (
        alt.Chart(senti_df)
        .mark_bar()
        .encode(
            alt.Y("Reflection by", title="Student", sort="-x"),
            alt.X("sentiment", title="Sentiment"),
            tooltip=[alt.Tooltip("sentiment", title="Sentiment")],
            opacity=alt.value(0.7),
            color=alt.value("red"),
        )
    )

    st.altair_chart(senti_plot)


def plot_question_sentiment(senti_df):
    """plot sentiment by student from a df containing name and senti"""
    senti_plot = (
        alt.Chart(senti_df)
        .mark_bar()
        .encode(
            alt.Y("questions", title="Questions", sort="-x"),
            alt.X("sentiment", title="Sentiment"),
            tooltip=[alt.Tooltip("sentiment", title="Sentiment")],
            opacity=alt.value(0.7),
            color=alt.value("red"),
        )
    )

    st.altair_chart(senti_plot)


def individual_student_freq(df_combined, freq_range):
    """page for individual student's word frequency"""
    students = st.multiselect(
        label="Select specific students below:",
        options=df_combined["Reflection by"]
    )
    # plot based on student selected
    # if students != "":
    #     for student in students:
    #         plot_frequency(
    #             az.word_frequency(
    #                 df_combined[df_combined["Reflection by"] == student]
    #                 .loc[:, ["combined"]]
    #                 .to_string(),
    #                 freq_range,
    #             )
    #         )

    freq_df = pd.DataFrame(columns=["student", "word", "freq"])
    st.write(freq_df)
    for student in students:
        individual_freq = az.word_frequency(
                        df_combined[df_combined["Reflection by"] == student]
                        .loc[:, ["combined"]]
                        .to_string(),
                        freq_range,
        )
        ind_df = pd.DataFrame(individual_freq, columns=["word", "freq"])
        ind_df["student"] = student
        freq_df = freq_df.append(ind_df)
    st.write(freq_df)

    # freq_df = pd.DataFrame(data, columns=["word", "freq"])
    # st.write(freq_df)

    # from altair.expr import datum
    #
    # freq_base = (
    #     alt.Chart(freq_df)
    #     .mark_bar()
    #     .encode(
    #         alt.Y("word", title="words", sort="-x"),
    #         alt.X("freq", title="frequencies"),
    #         tooltip=[alt.Tooltip("freq", title="frequency")],
    #         opacity=alt.value(0.7),
    #         color=alt.value("blue"),
    #     )
    # )

    # st.bar_chart(freq_df)
    # st.altair_chart(freq_plot)

    # chart = alt.hconcat()
    # for student in students:
    #     chart |= freq_base.transform_filter(datum.species == species)
    # chart

    # base = alt.Chart(df_combined).mark_point().encode(
    #         x='petalLength:Q',
    #         y='petalWidth:Q',
    #         color='species:N'
    #     ).properties(
    #         width=160,
    #         height=160
    #     )

    # chart = alt.hconcat()
    # for species in ['setosa', 'versicolor', 'virginica']:
    #     chart |= base.transform_filter(datum.species == species)
    # chart

    facet = alt.Chart(freq_df).mark_bar().encode(
        x='word',
        y='freq',
        column='student'
        ).properties(
            width=100,
            height=100
        )
    st.altair_chart(facet)



# def individual_student_freq(df_combined, freq_range):
#     """page for individual student's word frequency"""
#     students = st.multiselect(
#         label="Select specific students below:",
#         options=df_combined["Reflection by"]
#     )
#     # plot based on student selected
#     if students != "":
#         for student in students:
#             plot_frequency(
#                 az.word_frequency(
#                     df_combined[df_combined["Reflection by"] == student]
#                     .loc[:, ["combined"]]
#                     .to_string(),
#                     freq_range,
#                 )
#             )
#


def individual_question_freq(input_df, freq_range):
    """page for individual question's word frequency"""
    st.write(input_df)
    questions = st.multiselect(
        label="Select specific questions below:", options=input_df.columns[1:]
    )
    select_text = ""
    for column in questions:
        select_text += input_df[column].to_string(index=False)
    if select_text != "":
        plot_frequency(az.word_frequency(select_text, freq_range))


def plot_frequency(data: List[Tuple[str, int]]):
    """function to plot word frequency"""
    freq_df = pd.DataFrame(data, columns=["word", "freq"])
    # st.write(freq_df)

    freq_plot = (
        alt.Chart(freq_df)
        .mark_bar()
        .encode(
            alt.Y("word", title="words", sort="-x"),
            alt.X("freq", title="frequencies"),
            tooltip=[alt.Tooltip("freq", title="frequency")],
            opacity=alt.value(0.7),
            color=alt.value("blue"),
        ).properties(title='frequency plot')
    )

    # st.bar_chart(freq_df)
    st.altair_chart(freq_plot)


if __name__ == "__main__":
    main()