from typing import List, Tuple
from core.Searcher import Searcher
from concurrent.futures import ThreadPoolExecutor, as_completed

class SearcherController:
    def __init__(self, paralel_pages: int, visible_chrome: bool = True):
        self.paralel_pages = paralel_pages
        self.searchers_list: List[Searcher] = []
        self.splitted_list = []
        self.visible_chrome = visible_chrome
        
    @staticmethod
    def qtt_tests(pessoas):
        qtt = 0
        for i in range(len(pessoas)):
            add = 1
            pessoa = pessoas[i]
            only_digits = list(''.join(filter(str.isdigit, pessoa[0])))
            if "x" in str.lower(pessoa[0]):
                add*=len(Searcher.try_cpf(pessoa[0]))
            elif len(only_digits) == 10:
                to_search = set()
                for i in range(11):
                    only_digits_lis_copy = only_digits.copy()
                    only_digits_lis_copy.insert(i, "X")
                    new_cpfs = Searcher.try_cpf("".join(only_digits_lis_copy))
                    for new_cpf in new_cpfs:
                        to_search.add(new_cpf)
                add*=len(to_search)
            if "x" in str.lower(pessoa[1]):
                add*=len(Searcher.try_nasc(pessoa[1],[]))
            qtt+=add
        return qtt
        
    def start_pages(self):
        for _ in range(self.paralel_pages):
            new_searcher = Searcher(self.visible_chrome)
            self.searchers_list.append(new_searcher)
            
    def split_list(self, list: List[Tuple[str, str]]):
        if self.paralel_pages > len(list):
            self.paralel_pages = len(list)
        items_per_page = len(list)//self.paralel_pages
        for i in range(self.paralel_pages-1):
            sublist = list[i*items_per_page:(i+1)*items_per_page]
            self.splitted_list.append(sublist)
        sublist = list[(self.paralel_pages-1)*items_per_page:]
        self.splitted_list.append(sublist)
        
    def search_list(self, list: List[Tuple[str, str]], callback_result):
        def callback_subtitle(message):
            callback_result([],True,message)
        self.split_list(list)
        self.start_pages()
        
        def on_thread_done(future, searcher):
            searcher.close()
        
        with ThreadPoolExecutor(max_workers=self.paralel_pages) as executor:
            futures = []
            for i, searcher in enumerate(self.searchers_list):
                # callback(searcher.search_by_batch(self.splitted_list[i], callback_subtitle))
                future = executor.submit(searcher.search_by_batch, self.splitted_list[i], callback_subtitle)
                future.add_done_callback(lambda future, searcher=searcher: on_thread_done(future, searcher))
                futures.append(future)
                
            for future in as_completed(futures):
                callback_result(future.result())