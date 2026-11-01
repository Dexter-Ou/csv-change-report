# Multiline and Unicode regression

Run `python3 evaluation/test-multiline-unicode.py` from the product folder, with Python 3 and assertions enabled (no `-O`). No dependencies or network are used. The script also resolves the product from its own location, so it can be launched from another working directory.

The invented LF and CRLF inputs include quoted newlines, commas, doubled quotes, Unicode headers/values, reordered headers and reordered records. The static oracle was hand-calculated independently of product output: four records in each input, one added, one removed, two changed, one unchanged. Changed positions are before 1 / after 4 in 備考 and before 2 / after 2 in 名称; added after 3, removed before 4.

Exit 0 means detailed JSON, input hashes, batch counts/status, index states/links and reader inventory assertions passed. Reports and copied fixtures remain in the fresh temporary directory printed on stdout; remove it after inspection. This synthetic regression does not test browser accessibility, Windows/macOS behavior or crash durability.
