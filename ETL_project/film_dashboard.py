"""
Dashboard Interactif pour Film DataWarehouse - FIXED
Projet LE&BI - Analyse des Performances des Films
"""

import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# Configuration de style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ============================================================
# CONFIGURATION BASE DE DONNÉES
# ============================================================

DB_CONFIG = {
    'host': 'localhost',
    'database': 'MovieDW',
    'user': 'postgres',
    'password': 'admin123',
    'port': 5432
}

# ============================================================
# CONNEXION ET EXTRACTION DES DONNÉES
# ============================================================

def get_data():
    """Récupère toutes les données nécessaires pour le dashboard"""
    print("📊 Connexion à la base de données...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    # Requête principale - LOWERCASE column names for PostgreSQL
    query = """
    SELECT 
        f.filmid,
        f.title,
        f.certificate,
        d.directorname,
        s.studioname,
        g.genrename,
        c.countryname,
        l.languagename,
        t.year,
        t.quarter,
        t.month,
        fp.budgetdollars,
        fp.boxofficedollars,
        fp.profitdollars,
        fp.roi,
        fp.oscarnominations,
        fp.oscarwins,
        fp.runtimeminutes
    FROM factfilmperformance fp
    JOIN dimfilm f ON fp.filmid = f.filmid
    LEFT JOIN dimdirector d ON fp.directorid = d.directorid
    LEFT JOIN dimstudio s ON fp.studioid = s.studioid
    LEFT JOIN dimgenre g ON fp.genreid = g.genreid
    LEFT JOIN dimcountry c ON fp.countryid = c.countryid
    LEFT JOIN dimlanguage l ON fp.languageid = l.languageid
    LEFT JOIN dimtime t ON fp.timeid = t.timeid
    WHERE fp.boxofficedollars IS NOT NULL 
      AND fp.budgetdollars IS NOT NULL
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Rename columns to match original code (for consistency)
    df.columns = [
        'FilmID', 'Title', 'Certificate', 'DirectorName', 'StudioName',
        'GenreName', 'CountryName', 'LanguageName', 'Year', 'Quarter', 'Month',
        'BudgetDollars', 'BoxOfficeDollars', 'ProfitDollars', 'ROI',
        'OscarNominations', 'OscarWins', 'RunTimeMinutes'
    ]
    
    print(f"✅ {len(df)} films chargés pour l'analyse")
    print(f"📊 Colonnes: {list(df.columns)}")
    return df

# ============================================================
# ANALYSES ET VISUALISATIONS
# ============================================================

def create_dashboard(df):
    """Crée le tableau de bord complet"""
    
    # Créer une figure avec plusieurs sous-graphiques
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('📊 TABLEAU DE BORD - ANALYSE DE PERFORMANCE DES FILMS', 
                 fontsize=20, fontweight='bold', y=0.98)
    
    # Définir la grille
    gs = GridSpec(3, 3, figure=fig, hspace=0.3, wspace=0.3)
    
    # ============================================================
    # 1. TOP 10 FILMS PAR BOX OFFICE
    # ============================================================
    ax1 = fig.add_subplot(gs[0, :2])
    top10_films = df.nlargest(10, 'BoxOfficeDollars')[['Title', 'BoxOfficeDollars']]
    top10_films['BoxOffice_M'] = top10_films['BoxOfficeDollars'] / 1e6
    
    bars = ax1.barh(range(len(top10_films)), top10_films['BoxOffice_M'], 
                    color=plt.cm.viridis(np.linspace(0, 1, len(top10_films))))
    ax1.set_yticks(range(len(top10_films)))
    ax1.set_yticklabels(top10_films['Title'], fontsize=9)
    ax1.set_xlabel('Box Office (Millions $)', fontsize=10, fontweight='bold')
    ax1.set_title('🏆 TOP 10 - Films les Plus Rentables', fontsize=12, fontweight='bold')
    ax1.invert_yaxis()
    
    # Ajouter les valeurs
    for i, (idx, row) in enumerate(top10_films.iterrows()):
        ax1.text(row['BoxOffice_M'], i, f" ${row['BoxOffice_M']:.0f}M", 
                va='center', fontsize=8)
    
    # ============================================================
    # 2. KPIs PRINCIPAUX
    # ============================================================
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axis('off')
    
    # Calculer les KPIs
    total_films = len(df)
    total_budget = df['BudgetDollars'].sum() / 1e9
    total_boxoffice = df['BoxOfficeDollars'].sum() / 1e9
    avg_roi = df['ROI'].mean() * 100
    total_oscars = df['OscarWins'].sum()
    
    kpis_text = f"""
    📊 INDICATEURS CLÉS
    
    🎬 Films Analysés: {total_films:,}
    
    💰 Budget Total: ${total_budget:.2f}B
    
    💵 Box Office Total: ${total_boxoffice:.2f}B
    
    📈 ROI Moyen: {avg_roi:.1f}%
    
    🏆 Oscars Remportés: {int(total_oscars)}
    
    ⭐ Ratio Succès: {(total_boxoffice/total_budget):.2f}x
    """
    
    ax2.text(0.1, 0.5, kpis_text, fontsize=11, verticalalignment='center',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3),
             fontfamily='monospace')
    
    # ============================================================
    # 3. PERFORMANCE PAR GENRE
    # ============================================================
    ax3 = fig.add_subplot(gs[1, 0])
    
    genre_perf = df.groupby('GenreName').agg({
        'BoxOfficeDollars': 'sum',
        'FilmID': 'count'
    }).reset_index()
    genre_perf = genre_perf.nlargest(8, 'BoxOfficeDollars')
    genre_perf['BoxOffice_B'] = genre_perf['BoxOfficeDollars'] / 1e9
    
    ax3.bar(range(len(genre_perf)), genre_perf['BoxOffice_B'], 
            color=plt.cm.Spectral(np.linspace(0, 1, len(genre_perf))))
    ax3.set_xticks(range(len(genre_perf)))
    ax3.set_xticklabels(genre_perf['GenreName'], rotation=45, ha='right', fontsize=8)
    ax3.set_ylabel('Box Office (Milliards $)', fontsize=9, fontweight='bold')
    ax3.set_title('🎭 Performance par Genre', fontsize=11, fontweight='bold')
    ax3.grid(axis='y', alpha=0.3)
    
    # ============================================================
    # 4. BUDGET VS BOX OFFICE (Scatter)
    # ============================================================
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Échantillonner pour éviter surcharge
    sample_df = df.sample(min(200, len(df)))
    scatter = ax4.scatter(sample_df['BudgetDollars']/1e6, 
                         sample_df['BoxOfficeDollars']/1e6,
                         c=sample_df['ROI'], cmap='RdYlGn', 
                         alpha=0.6, s=50)
    
    # Ligne de référence (break-even)
    max_val = max(sample_df['BudgetDollars'].max(), sample_df['BoxOfficeDollars'].max())/1e6
    ax4.plot([0, max_val], [0, max_val], 'r--', alpha=0.5, label='Break-even')
    
    ax4.set_xlabel('Budget (Millions $)', fontsize=9, fontweight='bold')
    ax4.set_ylabel('Box Office (Millions $)', fontsize=9, fontweight='bold')
    ax4.set_title('💰 Budget vs Box Office', fontsize=11, fontweight='bold')
    ax4.legend()
    
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('ROI', fontsize=8)
    
    # ============================================================
    # 5. DISTRIBUTION ROI
    # ============================================================
    ax5 = fig.add_subplot(gs[1, 2])
    
    # Filtrer les ROI aberrants pour meilleure visualisation
    roi_filtered = df[df['ROI'].between(df['ROI'].quantile(0.05), 
                                          df['ROI'].quantile(0.95))]
    
    ax5.hist(roi_filtered['ROI']*100, bins=30, color='skyblue', edgecolor='black', alpha=0.7)
    ax5.axvline(roi_filtered['ROI'].mean()*100, color='red', 
                linestyle='--', linewidth=2, label=f'Moyenne: {roi_filtered["ROI"].mean()*100:.1f}%')
    ax5.set_xlabel('ROI (%)', fontsize=9, fontweight='bold')
    ax5.set_ylabel('Nombre de Films', fontsize=9, fontweight='bold')
    ax5.set_title('📈 Distribution du ROI', fontsize=11, fontweight='bold')
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)
    
    # ============================================================
    # 6. ÉVOLUTION TEMPORELLE
    # ============================================================
    ax6 = fig.add_subplot(gs[2, :2])
    
    if df['Year'].notna().any():
        yearly = df.groupby('Year').agg({
            'BoxOfficeDollars': 'sum',
            'BudgetDollars': 'sum',
            'FilmID': 'count'
        }).reset_index()
        
        ax6_2 = ax6.twinx()
        
        line1 = ax6.plot(yearly['Year'], yearly['BoxOfficeDollars']/1e9, 
                        marker='o', linewidth=2, color='green', label='Box Office')
        line2 = ax6.plot(yearly['Year'], yearly['BudgetDollars']/1e9, 
                        marker='s', linewidth=2, color='blue', label='Budget')
        line3 = ax6_2.plot(yearly['Year'], yearly['FilmID'], 
                          marker='^', linewidth=2, color='orange', 
                          linestyle='--', label='Nombre de Films')
        
        ax6.set_xlabel('Année', fontsize=9, fontweight='bold')
        ax6.set_ylabel('Montant (Milliards $)', fontsize=9, fontweight='bold', color='blue')
        ax6_2.set_ylabel('Nombre de Films', fontsize=9, fontweight='bold', color='orange')
        ax6.set_title('📅 Évolution Temporelle', fontsize=11, fontweight='bold')
        
        # Légende combinée
        lines = line1 + line2 + line3
        labels = [l.get_label() for l in lines]
        ax6.legend(lines, labels, loc='upper left')
        
        ax6.grid(alpha=0.3)
    else:
        ax6.text(0.5, 0.5, 'Données temporelles non disponibles', 
                ha='center', va='center', fontsize=12)
        ax6.axis('off')
    
    # ============================================================
    # 7. TOP RÉALISATEURS
    # ============================================================
    ax7 = fig.add_subplot(gs[2, 2])
    
    director_perf = df.groupby('DirectorName').agg({
        'BoxOfficeDollars': 'sum',
        'FilmID': 'count'
    }).reset_index()
    
    # Filtrer les réalisateurs avec au moins 2 films
    director_perf = director_perf[director_perf['FilmID'] >= 2]
    director_perf = director_perf.nlargest(10, 'BoxOfficeDollars')
    director_perf['BoxOffice_M'] = director_perf['BoxOfficeDollars'] / 1e6
    
    if len(director_perf) > 0:
        wedges, texts, autotexts = ax7.pie(
            director_perf['BoxOffice_M'].head(5), 
            labels=[name[:15] + '...' if len(name) > 15 else name 
                   for name in director_perf['DirectorName'].head(5)],
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 8}
        )
        ax7.set_title('🎬 Top 5 Réalisateurs\n(par Box Office)', 
                     fontsize=11, fontweight='bold')
    else:
        ax7.text(0.5, 0.5, 'Données réalisateurs\nnon disponibles', 
                ha='center', va='center', fontsize=10)
        ax7.axis('off')
    
    plt.tight_layout()
    return fig

# ============================================================
# ANALYSES COMPLÉMENTAIRES
# ============================================================

def print_insights(df):
    """Affiche des insights clés"""
    print("\n" + "="*60)
    print("🔍 INSIGHTS CLÉS POUR LE DÉCIDEUR")
    print("="*60)
    
    # 1. Film le plus rentable
    best_roi = df.loc[df['ROI'].idxmax()]
    print(f"\n🏆 Film le plus rentable (ROI):")
    print(f"   Titre: {best_roi['Title']}")
    print(f"   ROI: {best_roi['ROI']*100:.1f}%")
    print(f"   Budget: ${best_roi['BudgetDollars']/1e6:.1f}M")
    print(f"   Box Office: ${best_roi['BoxOfficeDollars']/1e6:.1f}M")
    
    # 2. Genre le plus rentable
    genre_roi = df.groupby('GenreName')['ROI'].mean().sort_values(ascending=False)
    print(f"\n🎭 Genre le plus rentable (ROI moyen):")
    print(f"   {genre_roi.index[0]}: {genre_roi.iloc[0]*100:.1f}%")
    
    # 3. Corrélation Budget-Oscars
    corr_budget_oscar = df[['BudgetDollars', 'OscarWins']].corr().iloc[0, 1]
    print(f"\n🏅 Corrélation Budget ↔ Oscars: {corr_budget_oscar:.3f}")
    if corr_budget_oscar > 0.3:
        print("   ➜ Un budget élevé augmente les chances d'Oscars")
    else:
        print("   ➜ Pas de corrélation forte entre budget et Oscars")
    
    # 4. Meilleur pays producteur
    country_perf = df.groupby('CountryName').agg({
        'BoxOfficeDollars': 'sum',
        'FilmID': 'count'
    }).sort_values('BoxOfficeDollars', ascending=False)
    
    if len(country_perf) > 0:
        print(f"\n🌍 Meilleur pays producteur:")
        print(f"   {country_perf.index[0]}: {country_perf.iloc[0]['FilmID']} films")
        print(f"   Box Office total: ${country_perf.iloc[0]['BoxOfficeDollars']/1e9:.2f}B")
    
    print("\n" + "="*60)

# ============================================================
# FONCTION PRINCIPALE
# ============================================================

def main():
    """Fonction principale pour générer le dashboard"""
    print("\n" + "="*60)
    print("📊 GÉNÉRATION DU TABLEAU DE BORD")
    print("="*60)
    
    try:
        # 1. Charger les données
        df = get_data()
        
        # 2. Créer le dashboard
        print("\n📈 Création des visualisations...")
        fig = create_dashboard(df)
        
        # 3. Sauvegarder
        output_file = 'Dashboard_Films.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n✅ Dashboard sauvegardé: {output_file}")
        
        # 4. Afficher les insights
        print_insights(df)
        
        # 5. Afficher le dashboard
        plt.show()
        
        print("\n" + "="*60)
        print("✅ DASHBOARD GÉNÉRÉ AVEC SUCCÈS!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# EXÉCUTION
# ============================================================

if __name__ == "__main__":
    main()