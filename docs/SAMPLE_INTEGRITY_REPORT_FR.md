# Rapport exemple - diagnostic d'integrite de backtest

**Nature :** demonstration entierement synthetique et reproductible  
**Auteur :** Nassim Berrahmane  
**Date :** 2026-09-06  
**Version auditee :** `public-sample-v1`
**Verdict global sur le jeu contamine :** `FAIL`

> Ce document montre la forme et le niveau de preuve d'un diagnostic borne. Il
> ne contient aucune donnee client, strategie privee, position, cle API ou
> observation du laboratoire de recherche.

## 1. Question d'audit

Le jeu de donnees fourni respecte-t-il les proprietes minimales de chronologie,
de cycle de vie des instruments et d'integrite des fichiers necessaires pour
defendre un resultat de backtest ?

Le diagnostic compare deux fixtures inspectables :

- une reference propre, utilisee comme controle positif ;
- une variante contaminee contenant exactement deux defauts deliberes.

L'audit ne cherche pas d'alpha et ne recalcule aucune performance.

## 2. Perimetre

| Element | Inclus | Resultat |
| --- | --- | --- |
| Manifestes SHA-256 | Oui | Verifies sur 3 fichiers par fixture |
| Schema tabulaire | Oui | Lisible et conforme |
| Chronologie feature -> decision | Oui | Un look-ahead detecte |
| Cycle de vie `(symbol, life_id)` | Oui | Une ligne post-cessation detectee |
| Doublons d'observations | Oui | Aucun dans cette fixture |
| Frais, spread, slippage et liquidite | Non | `NON VERIFIE` |
| Rendement, causalite et adequation au live | Non | Hors perimetre |

## 3. Methode reproductible

Deux executions hors ligne du meme auditeur ont ete realisees, sans reseau et
sans dependance a un compte de trading.

```powershell
python -m quant_integrity `
  --lives examples\clean\lives.csv `
  --market examples\clean\market.csv `
  --signals examples\clean\signals.csv `
  --manifest examples\clean\SHA256SUMS.txt
```

Resultat attendu et observe : `PASS`, code de sortie `0`, zero constat.

```powershell
python -m quant_integrity `
  --lives examples\lives.csv `
  --market examples\market.csv `
  --signals examples\signals.csv `
  --manifest examples\SHA256SUMS.txt
```

Resultat attendu et observe : `FAIL`, code de sortie `2`, deux constats.

## 4. Matrice de verdict

| Controle | Verdict | Preuve factuelle |
| --- | --- | --- |
| Integrite des fichiers | `PASS` | 3 entrees de manifeste verifiees |
| Catalogue des vies | `PASS` | 3 vies contractuelles controlees |
| Chronologie des signaux | `FAIL` | `LOOKAHEAD`, `signals.csv`, ligne 2 |
| Lignes apres cessation | `FAIL` | `PHANTOM_POST_CESSATION_ROW`, `market.csv`, ligne 3 |
| Separation des relistings | `PASS` | Cle composee `(symbol, life_id)` appliquee |
| Cout d'execution reel | `NON VERIFIE` | Aucun carnet, ordre ou bareme client fourni |

## 5. Constats prioritaires

### F-01 - Feature disponible apres la decision

**Gravite :** elevee  
**Code :** `LOOKAHEAD`  
**Preuve :** la fenetre de feature de `signals.csv`, ligne 2, se termine apres
le timestamp de decision.

**Impact plausible :** le signal utilise une information qui n'aurait pas ete
disponible au moment simule. La performance associee ne peut donc pas etre
defendue comme point-in-time. Aucun impact chiffre n'est affirme, car le
diagnostic ne recalcule pas les rendements.

**Correction minimale :** reconstruire la feature avec une borne temporelle
inferieure ou egale a la decision, puis regenerer le resultat depuis des entrees
figees.

### F-02 - Observation fantome apres cessation

**Gravite :** elevee  
**Code :** `PHANTOM_POST_CESSATION_ROW`  
**Preuve :** `market.csv`, ligne 3, contient une observation plate a volume nul
apres la cessation de `('ABCUSDT', 'life-1')`.

**Impact plausible :** une archive peut rendre tradable une observation qui ne
l'etait plus et melanger une ancienne vie avec un relisting ulterieur. Aucun
effet sur le PnL n'est quantifie dans ce diagnostic.

**Correction minimale :** exclure mecaniquement toute ligne exterieure a
`[life_start, cessation_at]` et conserver `life_id` dans toutes les jointures.

## 6. Tracabilite

| Fichier | SHA-256 |
| --- | --- |
| `examples/clean/lives.csv` | `981543F97A8DBCAB7DA29D4C29E667F25C26E153A9715A01ED7ED879E145FA5F` |
| `examples/clean/market.csv` | `F1D5DD52F6B012AC0E8522DFE292EFBD8CFE1E9E853E0090D81DE91391D6F51C` |
| `examples/clean/signals.csv` | `FDBCCD944A6573E6290E7FD859223E6274D985C2BA144C966C0B8DED0929D0B8` |
| `examples/market.csv` | `1DF2920DBCC1B7B8EFFB01C68841E9C49A7AEE61B40E0F037C9FCF0B54BB6DF5` |
| `examples/signals.csv` | `DF08E8A0DB144EF2FB91F6075E8B2F984D341762D01E5D33DEAEA43113465D2B` |

## 7. Conclusion

La fixture contaminee echoue pour deux raisons reproductibles et localisees.
La fixture propre passe les memes controles, ce qui montre que l'auditeur ne
rejette pas indistinctement toutes les entrees.

Ce verdict etablit uniquement des proprietes de donnees et de chronologie. Il
ne certifie ni l'exhaustivite d'une source reelle, ni un mecanisme economique,
ni une performance future, ni l'adequation au trading live.
