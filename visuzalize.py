"""
Schedule Visualizer with Violation Detection - Updated for 7-column format
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict

SLOTS_PER_DAY = 12
HALF = 6
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']

def slot_to_day_local(slot):
    """Global slot (1-indexed) -> (day_idx, local_slot 0-indexed)"""
    s = slot - 1
    return s // SLOTS_PER_DAY, s % SLOTS_PER_DAY

def slot_range(slot, duration):
    return set(range(slot, slot + duration))

def detect_conflicts(df):
    """
    Detect all constraint violations. 
    Dữ liệu df bây giờ đã có cột 'RoomCap' từ file viz.txt
    """
    conflicts = defaultdict(set)
    rows = df.reset_index(drop=True)
    n = len(rows)

    for i in range(n):
        ri = rows.iloc[i]
        slot = int(ri['Slot'])
        dur  = int(ri['Duration'])
        day_idx, local_start = slot_to_day_local(slot)

        # ── Capacity (Lấy trực tiếp từ cột RoomCap của dòng đó) ──────────────
        if ri['Attend'] > ri['RoomCap']:
            conflicts[i].add('capacity')

        # ── Day overflow ────────────────────────────────────────────────────
        local_end = local_start + dur - 1
        if local_end >= SLOTS_PER_DAY:
            conflicts[i].add('overflow')

        # ── Half-day boundary ───────────────────────────────────────────────
        if local_start < HALF and (local_start + dur) > HALF:
            conflicts[i].add('halfday')

        # ── Pairwise: room & teacher overlaps ────────────────────────────────
        slots_i = slot_range(slot, dur)
        for j in range(i + 1, n):
            rj = rows.iloc[j]
            slots_j = slot_range(int(rj['Slot']), int(rj['Duration']))
            if slots_i & slots_j:
                if ri['Room'] == rj['Room']:
                    conflicts[i].add('room')
                    conflicts[j].add('room')
                if ri['Teacher'] == rj['Teacher']:
                    conflicts[i].add('teacher')
                    conflicts[j].add('teacher')

    return conflicts

# Priority order for display color
_PRIORITY = ['overflow', 'halfday', 'room', 'teacher', 'capacity']
_COLORS = {
    'overflow': ('#AFA9EC', '#534AB7'),   # purple
    'halfday':  ('#ED93B1', '#993556'),   # pink
    'room':     ('#E24B4A', '#A32D2D'),   # red
    'teacher':  ('#EF9F27', '#854F0B'),   # amber
    'capacity': ('#FAC775', '#BA7517'),   # yellow
    'ok':       ('#5DCAA5', '#0F6E56'),   # teal
}

def bar_color(conflict_set):
    for tag in _PRIORITY:
        if tag in conflict_set:
            return _COLORS[tag]
    return _COLORS['ok']

def visualize_schedule(df, figsize=None):
    df = df.copy().reset_index(drop=True)
    conflicts = detect_conflicts(df)

    rooms = sorted(df['Room'].unique())
    n_rooms = len(rooms)
    room_idx = {r: i for i, r in enumerate(rooms)}

    ROW_H  = 1.0
    bar_h  = 0.72 * ROW_H
    total_height = n_rooms * ROW_H
    y_centers = [i * ROW_H for i in range(n_rooms)]

    if figsize is None:
        figsize = (22, max(5, n_rooms * 1.2 + 2.5))

    fig, axes = plt.subplots(1, 5, figsize=figsize, sharey=True, gridspec_kw={'wspace': 0.04})

    for day_idx, ax in enumerate(axes):
        ax.set_xlim(0, SLOTS_PER_DAY)
        ax.set_ylim(-ROW_H * 0.6, total_height - ROW_H * 0.4)
        ax.invert_yaxis()
        ax.set_title(DAYS[day_idx], fontsize=11, fontweight='normal', pad=6)
        ax.set_facecolor('#FAFAF9')

        for x in range(SLOTS_PER_DAY + 1):
            lw  = 1.5 if x == HALF else 0.5
            col = '#B4B2A9' if x == HALF else '#D3D1C7'
            ax.axvline(x, color=col, linewidth=lw, zorder=0)

        for yc in y_centers:
            ax.axhline(yc, color='#E8E6DF', linewidth=0.4, zorder=0)

        ax.text(HALF / 2, -ROW_H * 0.42, 'AM', ha='center', va='center', fontsize=7, color='#888780')
        ax.text(HALF + HALF / 2, -ROW_H * 0.42, 'PM', ha='center', va='center', fontsize=7, color='#888780')

        ax.set_xticks([x + 0.5 for x in range(SLOTS_PER_DAY)])
        ax.set_xticklabels([str(x + 1) for x in range(SLOTS_PER_DAY)], fontsize=7)
        ax.tick_params(axis='x', length=0)

        day_mask = df['Slot'].apply(lambda s: slot_to_day_local(s)[0] == day_idx)
        day_df = df[day_mask]

        for idx, row in day_df.iterrows():
            _, local_start = slot_to_day_local(row['Slot'])
            yc  = y_centers[room_idx[row['Room']]]
            dur = int(row['Duration'])
            fill, edge = bar_color(conflicts[idx])
            draw_w = min(dur, SLOTS_PER_DAY - local_start)

            patch = mpatches.FancyBboxPatch(
                (local_start, yc - bar_h / 2), draw_w, bar_h,
                boxstyle='round,pad=0.03', facecolor=fill, edgecolor=edge,
                linewidth=1.1, zorder=2, clip_on=True
            )
            ax.add_patch(patch)

            fs = max(5.5, min(8.5, draw_w * 3.2))
            label = f"C{row['ClassId']}\nT{row['Teacher']}"
            ax.text(local_start + draw_w / 2, yc, label, ha='center', va='center',
                    fontsize=fs, color='#2C2C2A', zorder=3, clip_on=True)

    axes[0].set_yticks(y_centers)
    axes[0].set_yticklabels([f'Room {r}' for r in rooms], fontsize=9)
    
    legend_patches = [
        mpatches.Patch(facecolor=_COLORS['ok'][0],       edgecolor=_COLORS['ok'][1],       label='OK'),
        mpatches.Patch(facecolor=_COLORS['room'][0],     edgecolor=_COLORS['room'][1],     label='Room conflict'),
        mpatches.Patch(facecolor=_COLORS['teacher'][0],  edgecolor=_COLORS['teacher'][1],  label='Teacher conflict'),
        mpatches.Patch(facecolor=_COLORS['capacity'][0], edgecolor=_COLORS['capacity'][1], label='Capacity exceeded'),
        mpatches.Patch(facecolor=_COLORS['overflow'][0], edgecolor=_COLORS['overflow'][1], label='Day overflow'),
        mpatches.Patch(facecolor=_COLORS['halfday'][0],  edgecolor=_COLORS['halfday'][1],  label='Half-day boundary crossed'),
    ]
    fig.legend(handles=legend_patches, loc='lower center', ncol=6, fontsize=8.5, frameon=False, bbox_to_anchor=(0.5, 0.03))

    counts = {tag: sum(1 for v in conflicts.values() if tag in v) for tag in _PRIORITY}
    fig.suptitle(f"Scheduled: {len(df)} | Room: {counts['room']} | Teacher: {counts['teacher']} | "
                 f"Cap: {counts['capacity']} | Overflow: {counts['overflow']} | Half-day: {counts['halfday']}",
                 fontsize=9.5, y=0.98, color='#444441')

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        fig.tight_layout()
    return fig, conflicts

if __name__ == '__main__':
    file_path_output = 'viz.txt'
    # Cập nhật thêm cột RoomCap (cột thứ 7)
    column_output = ['ClassId', 'Slot', 'Room', 'Duration', 'Teacher', 'Attend', 'RoomCap']

    df = pd.read_csv(
        file_path_output,
        sep=r'\s+',
        header=None,
        names=column_output,
        skiprows=1,      # Bỏ dòng FEASIBLE
        skipfooter=1,    # Bỏ dòng chứa danh sách capacity cuối cùng
        engine='python',
        dtype={c: int for c in column_output}
    )
    
    print("Dữ liệu lịch học đã xếp (7 lớp đầu tiên):")
    print(df.head())

    fig, conflicts = visualize_schedule(df)

    print("\n── Violation report ──")
    rows = df.reset_index(drop=True)
    for i, tags in conflicts.items():
        if tags:
            r = rows.iloc[i]
            print(f"  Class {r['ClassId']:3d} | slot={r['Slot']:2d} dur={r['Duration']} "
                  f"room={r['Room']} teacher={r['Teacher']} attend={r['Attend']}/{r['RoomCap']} "
                  f"→ {', '.join(sorted(tags))}")

    fig.savefig('schedule_viz.png', dpi=150, bbox_inches='tight')
    plt.show()