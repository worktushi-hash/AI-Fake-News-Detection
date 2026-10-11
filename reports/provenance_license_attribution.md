# Dataset Provenance, Licensing, and Attribution Notes

## 1. English Dataset (WELFake)
- **Source**: Zenodo Record 4561253 (Verma et al., 2021).
- **Components**: Merges Kaggle fake news, McIntire, ISOT fake news dataset, and GossipCop.
- **Licensing**: Open research dataset.
- **Attribution**: P. K. Verma, P. Agrawal, I. Amorim, R. Prodan, 'WELFake: Word Embedding Over Linguistic Features for Fake News Detection,' IEEE Transactions on Computational Social Systems, 2021. DOI: 10.1109/TCSS.2021.3068519.
- **Provenance Caution**: Published Zenodo metadata legend string (`0 = fake, 1 = real`) contradicts class counts (`35,028 real / 37,106 fake`). Target labels are retained as `unverified` and are NOT ready for verified supervised evaluation.

## 2. Hindi & Marathi Folder Corpora
- **Source**: Local folder structures (`Hindi_fake_news`/`Hindi_real_news` and `Marathi_fake_news`/`Marathi_real_news`).
- **Provenance Limitation**: Specific upstream web URLs, scraper manifests, or academic paper DOIs are **NOT** provided in the raw directory.
- **Licensing**: Unspecified / Research Use Only.
- **Attribution Note**: Folder labels represent claimed labels from folder names and are documented as `claimed_folder_label` in the output schema. Label reliability remains unverified independently.
