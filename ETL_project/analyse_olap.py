"""
Analyse OLAP pour Film DataWarehouse
Projet LE&BI - Opérations OLAP sur le Cube de données
"""

import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tabulate import tabulate
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'MovieDW',
    'user': 'postgres',
    'password': 'admin123',
    'port': 5432
}

# ============================================================
# CHARGEMENT DES DONNÉES DU CUBE
# ============================================================

def load_cube_data():
    """Charge les données pour créer le cube OLAP"""
    print("\n" + "="*70)
    print("📊 CHARGEMENT DU CUBE OLAP")
    print("="*70)
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Query avec lowercase pour PostgreSQL
    query = """
    SELECT 
        -- Dimensions
        g.genrename,
        c.countryname,
        t.year,
        t.quarter,
        d.directorname,
        
        -- Mesures (Measures)
        fp.budgetdollars,
        fp.boxofficedollars,
        fp.profitdollars,
        fp.roi,
        fp.oscarwins,
        fp.runtimeminutes,
        
        -- Identifiant
        f.filmid,
        f.title
        
    FROM factfilmperformance fp
    JOIN dimfilm f ON fp.filmid = f.filmid
    LEFT JOIN dimgenre g ON fp.genreid = g.genreid
    LEFT JOIN dimcountry c ON fp.countryid = c.countryid
    LEFT JOIN dimtime t ON fp.timeid = t.timeid
    LEFT JOIN dimdirector d ON fp.directorid = d.directorid
    WHERE fp.boxofficedollars IS NOT NULL 
      AND fp.budgetdollars IS NOT NULL
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Renommer les colonnes en PascalCase pour lisibilité
    df.columns = [
        'Genre', 'Country', 'Year', 'Quarter', 'Director',
        'Budget', 'BoxOffice', 'Profit', 'ROI', 'Oscars', 'Runtime',
        'FilmID', 'Title'
    ]
    
    print(f"✅ Cube chargé: {len(df)} enregistrements")
    print(f"📐 Dimensions: {df.columns[:5].tolist()}")
    print(f"📊 Mesures: {df.columns[5:11].tolist()}")
    
    return df

# ============================================================
# OPÉRATION OLAP 1: ROLL-UP (Agrégation)
# ============================================================

def olap_rollup(df):
    """
    ROLL-UP: Agrégation d'un niveau détaillé vers un niveau plus général
    Exemple: Quarter → Year (agrégation temporelle)
    """
    print("\n" + "="*70)
    print("🔼 OPÉRATION OLAP: ROLL-UP (Agrégation)")
    print("="*70)
    print("Description: Agrégation des données par Genre et Année")
    print("-"*70)
    
    # Niveau détaillé: Genre, Year, Quarter
    detailed = df.groupby(['Genre', 'Year', 'Quarter']).agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count'
    }).reset_index()
    detailed.columns = ['Genre', 'Year', 'Quarter', 'BoxOffice', 'Budget', 'NbFilms']
    
    print("\n📊 Niveau DÉTAILLÉ (Genre, Year, Quarter):")
    print(tabulate(detailed.head(10), headers='keys', tablefmt='grid', showindex=False))
    
    # ROLL-UP: Agrégation au niveau Genre, Year (suppression du Quarter)
    rolled_up = df.groupby(['Genre', 'Year']).agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count',
        'Profit': 'sum'
    }).reset_index()
    rolled_up.columns = ['Genre', 'Year', 'BoxOffice', 'Budget', 'NbFilms', 'Profit']
    rolled_up['ROI'] = (rolled_up['Profit'] / rolled_up['Budget']) * 100
    
    print("\n🔼 Niveau AGRÉGÉ (Genre, Year) - ROLL-UP:")
    print(tabulate(rolled_up.head(10), headers='keys', tablefmt='grid', 
                   showindex=False, floatfmt='.2f'))
    
    # Visualisation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1: Comparaison avant/après Roll-Up
    top_genres = rolled_up.groupby('Genre')['BoxOffice'].sum().nlargest(5).index
    rolled_up_top = rolled_up[rolled_up['Genre'].isin(top_genres)]
    
    for genre in top_genres:
        data = rolled_up_top[rolled_up_top['Genre'] == genre]
        ax1.plot(data['Year'], data['BoxOffice']/1e9, marker='o', label=genre, linewidth=2)
    
    ax1.set_xlabel('Année', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Box Office (Milliards $)', fontsize=12, fontweight='bold')
    ax1.set_title('📈 ROLL-UP: Évolution par Genre et Année', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Graphique 2: Total par Genre (super agrégation)
    genre_total = rolled_up.groupby('Genre')['BoxOffice'].sum().nlargest(8)
    ax2.barh(range(len(genre_total)), genre_total.values/1e9, 
             color=plt.cm.viridis(np.linspace(0, 1, len(genre_total))))
    ax2.set_yticks(range(len(genre_total)))
    ax2.set_yticklabels(genre_total.index)
    ax2.set_xlabel('Box Office Total (Milliards $)', fontsize=12, fontweight='bold')
    ax2.set_title('🔼 ROLL-UP Final: Total par Genre', fontsize=14, fontweight='bold')
    ax2.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig('OLAP_RollUp.png', dpi=300, bbox_inches='tight')
    print("\n✅ Visualisation sauvegardée: OLAP_RollUp.png")
    plt.show()
    
    return rolled_up

# ============================================================
# OPÉRATION OLAP 2: DRILL-DOWN (Détail)
# ============================================================

def olap_drilldown(df):
    """
    DRILL-DOWN: Descente d'un niveau agrégé vers un niveau plus détaillé
    Exemple: Genre → Genre + Country (ajout d'une dimension)
    """
    print("\n" + "="*70)
    print("🔽 OPÉRATION OLAP: DRILL-DOWN (Détail)")
    print("="*70)
    print("Description: Analyse détaillée par Genre puis par Pays")
    print("-"*70)
    
    # Niveau agrégé: Par Genre seulement
    aggregated = df.groupby('Genre').agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count'
    }).reset_index()
    aggregated.columns = ['Genre', 'BoxOffice', 'Budget', 'NbFilms']
    aggregated = aggregated.nlargest(5, 'BoxOffice')
    
    print("\n📊 Niveau AGRÉGÉ (Genre seulement):")
    print(tabulate(aggregated, headers='keys', tablefmt='grid', 
                   showindex=False, floatfmt='.2f'))
    
    # DRILL-DOWN: Ajout de la dimension Country
    drilled_down = df.groupby(['Genre', 'Country']).agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count',
        'Profit': 'sum'
    }).reset_index()
    drilled_down.columns = ['Genre', 'Country', 'BoxOffice', 'Budget', 'NbFilms', 'Profit']
    
    # Filtrer les top genres pour meilleure lisibilité
    top_genres = aggregated['Genre'].values
    drilled_down = drilled_down[drilled_down['Genre'].isin(top_genres)]
    drilled_down = drilled_down.nlargest(15, 'BoxOffice')
    
    print("\n🔽 Niveau DÉTAILLÉ (Genre + Country) - DRILL-DOWN:")
    print(tabulate(drilled_down, headers='keys', tablefmt='grid', 
                   showindex=False, floatfmt='.2f'))
    
    # Visualisation
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Préparer les données pour le graphique groupé
    pivot_data = drilled_down.pivot(index='Country', columns='Genre', values='BoxOffice').fillna(0)
    pivot_data = pivot_data.loc[pivot_data.sum(axis=1).nlargest(10).index]
    
    pivot_data.plot(kind='bar', ax=ax, width=0.8)
    ax.set_xlabel('Pays', fontsize=12, fontweight='bold')
    ax.set_ylabel('Box Office (Dollars)', fontsize=12, fontweight='bold')
    ax.set_title('🔽 DRILL-DOWN: Box Office par Genre et Pays', fontsize=14, fontweight='bold')
    ax.legend(title='Genre', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig('OLAP_DrillDown.png', dpi=300, bbox_inches='tight')
    print("\n✅ Visualisation sauvegardée: OLAP_DrillDown.png")
    plt.show()
    
    return drilled_down

# ============================================================
# OPÉRATION OLAP 3: SLICE (Coupe)
# ============================================================

def olap_slice(df):
    """
    SLICE: Sélection d'une seule valeur sur une dimension
    Exemple: Sélectionner uniquement l'année 2010
    """
    print("\n" + "="*70)
    print("🔪 OPÉRATION OLAP: SLICE (Coupe)")
    print("="*70)
    print("Description: Analyse pour l'année 2010 uniquement")
    print("-"*70)
    
    # Afficher les années disponibles
    years_available = df['Year'].dropna().unique()
    print(f"\n📅 Années disponibles dans le cube: {sorted(years_available)}")
    
    # SLICE: Filtrer pour Year = 2010
    year_to_slice = 2010
    if year_to_slice not in years_available:
        year_to_slice = int(sorted(years_available)[len(years_available)//2])  # Année médiane
        print(f"⚠️  2010 non disponible, utilisation de {year_to_slice}")
    
    sliced_data = df[df['Year'] == year_to_slice].copy()
    
    print(f"\n🔪 SLICE appliqué: Year = {year_to_slice}")
    print(f"📊 Nombre d'enregistrements après SLICE: {len(sliced_data)}")
    
    # Analyse du slice
    slice_analysis = sliced_data.groupby('Genre').agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count',
        'Oscars': 'sum'
    }).reset_index()
    slice_analysis.columns = ['Genre', 'BoxOffice', 'Budget', 'NbFilms', 'Oscars']
    slice_analysis = slice_analysis.nlargest(10, 'BoxOffice')
    
    print(f"\n📊 Analyse pour l'année {year_to_slice}:")
    print(tabulate(slice_analysis, headers='keys', tablefmt='grid', 
                   showindex=False, floatfmt='.2f'))
    
    # Visualisation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1: Box Office par Genre
    ax1.bar(range(len(slice_analysis)), slice_analysis['BoxOffice']/1e9,
            color=plt.cm.plasma(np.linspace(0, 1, len(slice_analysis))))
    ax1.set_xticks(range(len(slice_analysis)))
    ax1.set_xticklabels(slice_analysis['Genre'], rotation=45, ha='right')
    ax1.set_ylabel('Box Office (Milliards $)', fontsize=12, fontweight='bold')
    ax1.set_title(f'🔪 SLICE: Box Office par Genre ({year_to_slice})', 
                  fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Graphique 2: Budget vs Box Office
    ax2.scatter(slice_analysis['Budget']/1e6, slice_analysis['BoxOffice']/1e6,
                s=slice_analysis['NbFilms']*50, alpha=0.6,
                c=range(len(slice_analysis)), cmap='viridis')
    
    for i, row in slice_analysis.iterrows():
        ax2.annotate(row['Genre'][:10], 
                    (row['Budget']/1e6, row['BoxOffice']/1e6),
                    fontsize=8, alpha=0.7)
    
    ax2.set_xlabel('Budget (Millions $)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Box Office (Millions $)', fontsize=12, fontweight='bold')
    ax2.set_title(f'🔪 SLICE: Budget vs Box Office ({year_to_slice})', 
                  fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('OLAP_Slice.png', dpi=300, bbox_inches='tight')
    print("\n✅ Visualisation sauvegardée: OLAP_Slice.png")
    plt.show()
    
    return sliced_data

# ============================================================
# OPÉRATION OLAP 4: DICE (Découpage)
# ============================================================

def olap_dice(df):
    """
    DICE: Sélection de plusieurs valeurs sur plusieurs dimensions
    Exemple: Genre in ['Genre_X', 'Genre_Y'] AND Year in [2008, 2009, 2010]
    """
    print("\n" + "="*70)
    print("🎲 OPÉRATION OLAP: DICE (Découpage)")
    print("="*70)
    print("Description: Filtrage multiple sur Genre et Année")
    print("-"*70)
    
    # Identifier les top genres
    top_genres = df.groupby('Genre')['BoxOffice'].sum().nlargest(3).index.tolist()
    
    # Identifier les années avec le plus de données
    top_years = df['Year'].value_counts().nlargest(3).index.tolist()
    
    print(f"\n🎲 Critères du DICE:")
    print(f"   - Genres: {top_genres}")
    print(f"   - Années: {top_years}")
    
    # DICE: Filtrage multiple
    diced_data = df[
        (df['Genre'].isin(top_genres)) & 
        (df['Year'].isin(top_years))
    ].copy()
    
    print(f"\n📊 Nombre d'enregistrements après DICE: {len(diced_data)}")
    print(f"📊 Réduction: {len(df)} → {len(diced_data)} ({len(diced_data)/len(df)*100:.1f}%)")
    
    # Analyse du dice
    dice_analysis = diced_data.groupby(['Genre', 'Year']).agg({
        'BoxOffice': 'sum',
        'Budget': 'sum',
        'FilmID': 'count',
        'ROI': 'mean'
    }).reset_index()
    dice_analysis.columns = ['Genre', 'Year', 'BoxOffice', 'Budget', 'NbFilms', 'ROI_Moyen']
    
    print("\n📊 Analyse après DICE:")
    print(tabulate(dice_analysis, headers='keys', tablefmt='grid', 
                   showindex=False, floatfmt='.2f'))
    
    # Visualisation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Graphique 1: Evolution par Genre
    for genre in top_genres:
        data = dice_analysis[dice_analysis['Genre'] == genre]
        ax1.plot(data['Year'], data['BoxOffice']/1e9, 
                marker='o', linewidth=2, label=genre, markersize=8)
    
    ax1.set_xlabel('Année', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Box Office (Milliards $)', fontsize=12, fontweight='bold')
    ax1.set_title('🎲 DICE: Évolution Box Office (Genres & Années sélectionnés)', 
                  fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(alpha=0.3)
    
    # Graphique 2: Heatmap
    pivot_heatmap = dice_analysis.pivot(index='Genre', columns='Year', values='BoxOffice')
    sns.heatmap(pivot_heatmap, annot=True, fmt='.2e', cmap='YlOrRd', 
                ax=ax2, cbar_kws={'label': 'Box Office ($)'})
    ax2.set_title('🎲 DICE: Heatmap Box Office', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('OLAP_Dice.png', dpi=300, bbox_inches='tight')
    print("\n✅ Visualisation sauvegardée: OLAP_Dice.png")
    plt.show()
    
    return diced_data

# ============================================================
# OPÉRATION OLAP 5: PIVOT (Rotation)
# ============================================================

def olap_pivot(df):
    """
    PIVOT: Rotation des axes du cube pour changer de perspective
    Exemple: Changer Genre (lignes) et Year (colonnes) 
    """
    print("\n" + "="*70)
    print("🔄 OPÉRATION OLAP: PIVOT (Rotation)")
    print("="*70)
    print("Description: Rotation des dimensions pour différentes perspectives")
    print("-"*70)
    
    # Vue 1: Genre en lignes, Year en colonnes
    pivot1 = df.groupby(['Genre', 'Year'])['BoxOffice'].sum().unstack(fill_value=0)
    pivot1 = pivot1.loc[pivot1.sum(axis=1).nlargest(8).index]
    
    print("\n📊 PIVOT 1: Genre (lignes) × Year (colonnes)")
    print(pivot1.head(8))
    
    # Vue 2: ROTATION - Year en lignes, Genre en colonnes
    pivot2 = df.groupby(['Year', 'Genre'])['BoxOffice'].sum().unstack(fill_value=0)
    pivot2 = pivot2[pivot2.sum(axis=0).nlargest(8).index]
    
    print("\n🔄 PIVOT 2 (Rotation): Year (lignes) × Genre (colonnes)")
    print(pivot2.head(10))
    
    # Visualisation
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    
    # Graphique 1: Heatmap Vue 1
    sns.heatmap(pivot1/1e9, annot=False, cmap='Blues', ax=ax1, 
                cbar_kws={'label': 'Box Office (Milliards $)'})
    ax1.set_title('🔄 PIVOT Vue 1: Genre × Year', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Année', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Genre', fontsize=12, fontweight='bold')
    
    # Graphique 2: Heatmap Vue 2 (Rotation)
    sns.heatmap(pivot2/1e9, annot=False, cmap='Greens', ax=ax2,
                cbar_kws={'label': 'Box Office (Milliards $)'})
    ax2.set_title('🔄 PIVOT Vue 2 (Rotation): Year × Genre', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Genre', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Année', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('OLAP_Pivot.png', dpi=300, bbox_inches='tight')
    print("\n✅ Visualisation sauvegardée: OLAP_Pivot.png")
    plt.show()
    
    return pivot1, pivot2

# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def main():
    """Exécution de toutes les opérations OLAP"""
    print("\n" + "="*70)
    print("🎯 ANALYSE OLAP - FILM DATAWAREHOUSE")
    print("="*70)
    
    try:
        # Charger le cube
        df = load_cube_data()
        
        # Opération 1: ROLL-UP
        rolled_up = olap_rollup(df)
        
        # Opération 2: DRILL-DOWN
        drilled_down = olap_drilldown(df)
        
        # Opération 3: SLICE
        sliced = olap_slice(df)
        
        # Opération 4: DICE
        diced = olap_dice(df)
        
        # Opération 5: PIVOT
        pivot1, pivot2 = olap_pivot(df)
        
        # Résumé
        print("\n" + "="*70)
        print("✅ ANALYSE OLAP TERMINÉE AVEC SUCCÈS!")
        print("="*70)
        print("\n📊 Opérations OLAP réalisées:")
        print("   1. ✅ ROLL-UP (Agrégation)")
        print("   2. ✅ DRILL-DOWN (Détail)")
        print("   3. ✅ SLICE (Coupe)")
        print("   4. ✅ DICE (Découpage)")
        print("   5. ✅ PIVOT (Rotation)")
        print("\n📁 Fichiers générés:")
        print("   - OLAP_RollUp.png")
        print("   - OLAP_DrillDown.png")
        print("   - OLAP_Slice.png")
        print("   - OLAP_Dice.png")
        print("   - OLAP_Pivot.png")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# EXÉCUTION
# ============================================================

if __name__ == "__main__":
    main()