import os

from app.test.fixtures import app, db  # noqa

from .service import KlangService

folder_name = "data_test"
project_name = "project1"
sample_name = "sample1"
file_name = "John_Doe"


def test_get_path_data():
    path_data = KlangService.get_path_data()
    assert os.path.isdir(path_data)


def test_get_path_project():
    path_project = KlangService.get_path_project(project_name)
    assert os.path.isdir(path_project)
    assert path_project.endswith(project_name)


def test_get_path_project_samples():
    path_samples = KlangService.get_path_project_samples(project_name)
    assert os.path.isdir(path_samples)


def test_get_path_project_sample():
    path_sample = KlangService.get_path_project_sample(project_name, sample_name)
    assert os.path.isdir(path_sample)
    assert path_sample.endswith(sample_name)


def test_get_path_project_sample_conll():
    path_sample_conll = KlangService.get_path_project_sample_conll(project_name, sample_name)
    assert os.path.isfile(path_sample_conll)
    assert path_sample_conll.endswith(".conll")


def test_get_projects():
    projects = KlangService.get_projects()
    assert projects == ["project1"]


def test_get_project_samples():
    samples = KlangService.get_project_samples(project_name)
    assert samples == ["sample1"]


def test_read_conll():
    path_sample_conll = KlangService.get_path_project_sample_conll(project_name, sample_name)
    conll_string = KlangService.read_conll(path_sample_conll)
    assert type(conll_string) == str

def test_get_project_sample_conll():
    conll = KlangService.get_project_sample_conll(project_name, sample_name)
    assert conll == "# sent_id = John_Doe.intervals.conll__1\n# text = it is\n# sound_url = John_Doe.wav\n1	it	it	_	_	_	_	_	_	AlignBegin=100|AlignEnd=500\n2	is	is	_	_	_	_	_	_	AlignBegin=600|AlignEnd=1000"


# def test_get_all():
#     conlls = KlangService.get_all_name()
#     assert conlls == ["John_Doe"]


# def test_get_by_name():
#     path_conll = KlangService.get_path_conll(file_name)
#     conll_string = KlangService.read_conll(path_conll)
#     assert conll_string == KlangService.get_by_name(file_name)


def test_conll_to_sentences():
    conll_string = "# sent_id = test_sentence_1\n1\ttest_token\ntest_lemma\ntest_upos\n\n# sent_id = test_sentence_2\n1\ttest_token\ntest_lemma\ntest_upos\n\n"
    sentences = KlangService.conll_to_sentences(conll_string)
    assert len(sentences) == 2


def test_sentence_to_audio_tokens():
    sentence = "# sent_id = test_sentence_1\n1\tdonc\tdonc\t_\t_\t_\t_\t_\t_\tAlignBegin=0|AlignEnd=454"
    audio_tokens = KlangService.sentence_to_audio_tokens(sentence)
    assert audio_tokens[0][0] == "donc"
    assert audio_tokens[0][1] == "0"
    assert audio_tokens[0][2] == "454"
    ## these three following lines are an example of what we should get
    # assert audio_tokens[0]["token"] == "donc"
    # assert audio_tokens[0]["alignBegin"] == 0
    # assert audio_tokens[0]["alignEnd"] == 454

def test_compute_conll_audio_tokens():
    path_conll = KlangService.get_path_project_sample_conll(project_name, sample_name)
    conll = KlangService.read_conll(path_conll)
    conll_audio_tokens = KlangService.compute_conll_audio_tokens(conll)
    assert len(conll_audio_tokens) == 1

# when we will have new structure, we can use this
# def test_process_sentences_audio_token():
#     sentences_audio_token = KlangService.process_sentences_audio_token(file_name)
#     assert sentences_audio_token == [{
#         1: {"token": "it", "alignBegin": 100, "alignEnd": 500},
#         2: {"token": "is", "alignBegin": 600, "alignEnd": 1000}
#     }]
