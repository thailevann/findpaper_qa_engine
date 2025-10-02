Data loaded: (66, 16)
   idx key_ingredients_id                                           question  ...  quality_efficiency_score  overall_quality_category  time_category
0    1                  1  What publicly available datasets are typically...  ...                  0.160000                      poor           fast
1    1                  2  What publicly available datasets are typically...  ...                  0.090000                      poor           fast
2    8                  1  What are advantages and disadvantages of top m...  ...                  0.265000                      poor           fast
3    8                  2  What are advantages and disadvantages of top m...  ...                  0.265000                      poor           fast
4   11                  1  How do large language models like ChatGPT impa...  ...                  0.364167                      poor           fast

[5 rows x 16 columns]
Top 10 worst answers:
    idx                                           question  overall_quality_score
1     1  What publicly available datasets are typically...               0.000000
0     1  What publicly available datasets are typically...               0.100000
27   44  What are some systems papers that conduct an o...               0.100000
61   96  How does the tree covering technique differ in...               0.150000
47   82  What is a good Ontology semantic similarity me...               0.150000
60   96  How does the tree covering technique differ in...               0.166667
26   44  What are some systems papers that conduct an o...               0.200000
33   60  What are existing methods to elicit user inten...               0.208333
25   37  what are the best recent techniques for text w...               0.208333
65   98  Does active learning work well when fine-tunin...               0.208333
Top 10 lowest relevance passages:
    idx                                           question  relevance_score
0     1  What publicly available datasets are typically...              0.0
1     1  What publicly available datasets are typically...              0.0
26   44  What are some systems papers that conduct an o...              0.0
27   44  What are some systems papers that conduct an o...              0.0
2     8  What are advantages and disadvantages of top m...              0.1
3     8  What are advantages and disadvantages of top m...              0.1
61   96  How does the tree covering technique differ in...              0.1
60   96  How does the tree covering technique differ in...              0.1
47   82  What is a good Ontology semantic similarity me...              0.1
34   62  Are there papers that use different formats of...              0.1
Cluster Summary:
               correctness_score  coverage_score  reasoning_score
error_cluster
0                       0.335000        0.230000         0.315000
1                       0.772222        0.666667         0.733333
2                       0.732143        0.628571         0.696429
Correlation between time and quality: 0.115
Slow and poor quality answers:
    idx                                           question  elapsed_time_sec  overall_quality_score
0     1  What publicly available datasets are typically...         46.922830               0.100000
1     1  What publicly available datasets are typically...         46.922830               0.000000
2     8  What are advantages and disadvantages of top m...         43.761962               0.250000
3     8  What are advantages and disadvantages of top m...         43.761962               0.250000
4    11  How do large language models like ChatGPT impa...         46.937262               0.391667
5    11  How do large language models like ChatGPT impa...         46.937262               0.383333
6    12  What are good practices for detecting AI-gener...         33.194209               0.491667
7    12  What are good practices for detecting AI-gener...         33.194209               0.458333
11   14  Describe what is known about overfitting in in...         37.923005               0.400000
16   22  How do different fairness metrics correlate wi...         32.740008               0.458333
18   27  What datasets and methods are used to pre-trai...         41.275413               0.458333
19   27  What datasets and methods are used to pre-trai...         41.275413               0.233333
22   33  is there any evidence that large language mode...         35.250911               0.466667
23   33  is there any evidence that large language mode...         35.250911               0.300000
24   37  what are the best recent techniques for text w...         39.712160               0.341667
25   37  what are the best recent techniques for text w...         39.712160               0.208333
26   44  What are some systems papers that conduct an o...         37.324202               0.200000
27   44  What are some systems papers that conduct an o...         37.324202               0.100000
28   56  What interfaces have researchers developed to ...         36.462893               0.441667
29   56  What interfaces have researchers developed to ...         36.462893               0.233333
31   58  What interfaces have researchers developed for...         40.510611               0.358333
32   60  What are existing methods to elicit user inten...         35.584817               0.458333
33   60  What are existing methods to elicit user inten...         35.584817               0.208333
34   62  Are there papers that use different formats of...         34.216069               0.250000
35   62  Are there papers that use different formats of...         34.216069               0.233333
40   78  Have large langauge models been applied to the...         41.056313               0.491667
41   78  Have large langauge models been applied to the...         41.056313               0.333333
48   85  How can I use an hybridization of ontology and...         32.887329               0.458333
49   85  How can I use an hybridization of ontology and...         32.887329               0.425000
52   91  How can question generation be used to mitigat...         36.844911               0.491667
53   91  How can question generation be used to mitigat...         36.844911               0.275000
55   92  What are some of the challenges associated wit...         45.992869               0.458333
58   94  During pre-training, why is the transformer em...         39.215150               0.483333
60   96  How does the tree covering technique differ in...         35.391811               0.166667
61   96  How does the tree covering technique differ in...         35.391811               0.150000
62   97  What are the leading approaches to automatic s...         56.615970               0.491667
64   98  Does active learning work well when fine-tunin...         33.795138               0.491667
65   98  Does active learning work well when fine-tunin...         33.795138               0.208333

Analysis completed! Outputs saved in: analysis_outputs