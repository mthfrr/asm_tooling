import os

class Student():
    def __init__(self,
                 login,
                 gitpath,
                 project_dir,
                 root_folder,
                 archi_file_list,
                 global_allowed_files,
                 exos):
        self.login = login
        self.cri = f"https://cri.epita.fr/users/{login}/"
        self.gitpath = gitpath
        self.project_dir = project_dir
        self.root_folder = root_folder
        self.archi_file_list = archi_file_list
        self.global_allowed_files = global_allowed_files
        
        # computed
        self.file_list = []
        self.commits = None
        self.exos = exos
        self.tree = ""
        self.trace = "not enable"
        
        # state
        self.has_dir = os.path.isdir(self.project_dir)
        
        # tests
        self.has_cloned = self.has_dir
        self.is_empty = None
        self.AUTHORS = None
        self.trash_files = None
        self.missing_files = None
        self.empty_or_missing_files = None
        
        
        
        
        