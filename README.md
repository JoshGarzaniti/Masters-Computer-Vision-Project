How to run Code from this project

1: First use the Matsers_Past_Participants python file to scrape past tournaments and historical records (note that if using this file >=2026 you will need to edit the the 2025 lines to 2026 
(there was an issue picking up the first two years of each era so I ran one section to grab the first year individually, scrape the rest of the years and go back and manually scrape the second year)...working on a patch

2: Use the data cleaning file *to be created* (also python) to scrub the imported masters_players.csv file (Important note there's a case in the data where one player had multiple scores during day 3 (78,81)...this will show up in the R3 data so before you load in the excel file, either go in and manually change it so that his first round was 78, and his 3rd was 81 (since he was making up for day 1) or clean in explicitely in the data cleaning jupyter file).

3: Run the Masters_Vault_Scraping python file *to be created* and scrape all of the final round shot videos from relevant 1968 players through 2025.

Combine the vault videos and the Finalized Masters Participants dataframe into one final df for contextual analysis
