import re
from typing import List, Dict, Any

class BiblicalReferenceDetector:
    def __init__(self):
        # Common Chinese Bible book names and their variations
        self.bible_books = {
            "创世记": ["创世纪", "创"],
            "出埃及记": ["出埃及", "出"],
            "利未记": ["利未", "利"],
            "民数记": ["民数", "民"],
            "申命记": ["申命", "申"],
            "约书亚记": ["约书亚", "书"],
            "士师记": ["士师", "士"],
            "路得记": ["路得", "得"],
            "撒母耳记上": ["撒上"],
            "撒母耳记下": ["撒下"],
            "列王纪上": ["王上"],
            "列王纪下": ["王下"],
            "历代志上": ["代上"],
            "历代志下": ["代下"],
            "以斯拉记": ["以斯拉", "拉"],
            "尼希米记": ["尼希米", "尼"],
            "以斯帖记": ["以斯帖", "斯"],
            "约伯记": ["约伯", "伯"],
            "诗篇": ["诗"],
            "箴言": ["箴"],
            "传道书": ["传道", "传"],
            "雅歌": ["歌"],
            "以赛亚书": ["以赛亚", "赛"],
            "耶利米书": ["耶利米", "耶"],
            "耶利米哀歌": ["哀歌", "哀"],
            "以西结书": ["以西结", "结"],
            "但以理书": ["但以理", "但"],
            "何西阿书": ["何西阿", "何"],
            "约珥书": ["约珥", "珥"],
            "阿摩司书": ["阿摩司", "摩"],
            "俄巴底亚书": ["俄巴底亚", "俄"],
            "约拿书": ["约拿", "拿"],
            "弥迦书": ["弥迦", "弥"],
            "那鸿书": ["那鸿", "鸿"],
            "哈巴谷书": ["哈巴谷", "哈"],
            "西番雅书": ["西番雅", "番"],
            "哈该书": ["哈该", "该"],
            "撒迦利亚书": ["撒迦利亚", "亚"],
            "玛拉基书": ["玛拉基", "玛"],
            "马太福音": ["马太", "太"],
            "马可福音": ["马可", "可"],
            "路加福音": ["路加", "路"],
            "约翰福音": ["约翰", "约"],
            "使徒行传": ["使徒", "徒"],
            "罗马书": ["罗马", "罗"],
            "哥林多前书": ["林前"],
            "哥林多后书": ["林后"],
            "加拉太书": ["加拉太", "加"],
            "以弗所书": ["以弗所", "弗"],
            "腓立比书": ["腓立比", "腓"],
            "歌罗西书": ["歌罗西", "西"],
            "帖撒罗尼迦前书": ["帖前"],
            "帖撒罗尼迦后书": ["帖后"],
            "提摩太前书": ["提前"],
            "提摩太后书": ["提后"],
            "提多书": ["提多", "多"],
            "腓利门书": ["腓利门", "门"],
            "希伯来书": ["希伯来", "来"],
            "雅各书": ["雅各", "雅"],
            "彼得前书": ["彼前"],
            "彼得后书": ["彼后"],
            "约翰一书": ["约一"],
            "约翰二书": ["约二"],
            "约翰三书": ["约三"],
            "犹大书": ["犹大", "犹"],
            "启示录": ["启示", "启"]
        }
        
        # Build regex pattern for all book names and their variations
        book_patterns = []
        for book, variations in self.bible_books.items():
            patterns = [re.escape(book)] + [re.escape(v) for v in variations]
            book_patterns.extend(patterns)
        
        # Chinese number characters
        chinese_nums = "一二三四五六七八九十百"
        
        # Pattern for chapter and verse references
        # Matches patterns like:
        # - 约翰福音3:16
        # - 约翰福音 三章十六节
        # - 约3:16
        # - 约三16
        # - 腓立比书4:6
        self.reference_pattern = fr"""
            [（(]?                        # Optional opening parenthesis
            (?:{'|'.join(book_patterns)})  # Book name
            \s*                            # Optional whitespace
            (?:                           # Chapter-verse group
                [0-9]+                    # Chapter number
                [:：]                      # Colon (Chinese or English)
                [0-9]+                    # Verse number
            )
            [）)]?                        # Optional closing parenthesis
        """

    def find_references(self, text: str) -> List[str]:
        """
        Find all biblical references in the given text.
        Returns a list of reference strings.
        """
        references = []
        # Add debug print
        print(f"Searching for biblical references in text: {text}")
        for match in re.finditer(self.reference_pattern, text, re.VERBOSE):
            ref = match.group(0)
            print(f"Found reference: {ref}")
            references.append(ref)
        if not references:
            print("No references found")
        return references

    def contains_references(self, text: str) -> bool:
        """
        Check if the text contains any biblical references.
        """
        return bool(re.search(self.reference_pattern, text, re.VERBOSE))
