import networkx as nx
import matplotlib.pyplot as plt
import aiosqlite
from config import DB_PATH
from datetime import datetime


async def generate_graph():
    """Generate a directed graph of inviters and invitees."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT inviter_id, invited_id FROM invited_users")
        edges = await cursor.fetchall()

    G = nx.DiGraph()
    for inviter, invited in edges:
        G.add_edge(inviter, invited)

    if G.number_of_nodes() == 0:
        # Create a placeholder image with a message
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.text(0.5, 0.5, "هیچ دعوتی ثبت نشده است", ha='center', va='center', fontsize=14)
        ax.axis('off')
        img_path = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(img_path, dpi=100)
        plt.close()
        return img_path

    # Draw graph
    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    nx.draw(G, pos, with_labels=True, node_color='lightblue',
            edge_color='gray', arrows=True, arrowstyle='->', arrowsize=10,
            font_size=8, node_size=500)
    plt.title("شبکه دعوت‌ها")
    plt.tight_layout()
    img_path = f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(img_path, dpi=150)
    plt.close()
    return img_path