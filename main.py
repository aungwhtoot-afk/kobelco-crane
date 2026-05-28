import flet as ft  # စာလုံးအသေး ပြင်ဆင်ပြီး
import math

# Kobelco RK250 Load Chart Data (မူရင်းဒေတာများအတိုင်း အတိအကျဖြစ်ပါသည်)
max_front_caps = {
    9.32:  {3.0: 25.0, 4.0: 23.0, 5.0: 19.4, 6.0: 16.3},
    16.42: {5.0: 16.7, 8.0: 10.9, 10.0: 7.4, 12.0: 5.45},
    23.52: {6.0: 11.2, 10.0: 7.05, 14.0: 4.15, 16.0: 3.45},
    30.62: {8.0: 7.0, 12.0: 4.95, 16.0: 3.15, 20.0: 1.9, 24.0: 1.15}
}

crane_database = {
    6.3: {
        "360": max_front_caps
    },
    5.9: {
        "front": max_front_caps,
        "side": {
            9.32:  {3.0: 25.0, 4.0: 23.0, 5.0: 19.4, 6.0: 15.1},
            16.42: {5.0: 16.7, 8.0: 10.95, 10.0: 6.9, 12.0: 4.9},
            23.52: {6.0: 11.2, 10.0: 6.9, 14.0: 4.0, 16.0: 3.0},
            30.62: {8.0: 7.0, 12.0: 4.9, 16.0: 3.0, 20.0: 1.65}
        }
    },
    5.1: {
        "front": max_front_caps,
        "side": {
            9.32:  {3.0: 25.0, 4.0: 23.0, 5.0: 18.1, 6.0: 12.9},
            16.42: {5.0: 15.6, 8.0: 9.65, 10.0: 6.20, 12.0: 4.30},
            23.52: {6.0: 11.2, 10.0: 6.90, 14.0: 3.75, 16.0: 2.80},
            30.62: {8.0: 7.0, 12.0: 4.90, 16.0: 3.00, 20.0: 1.65, 24.0: 0.90}
        }
    },
    3.8: {
        "front": max_front_caps,
        "side": {
            9.32:  {3.0: 25.0, 4.0: 15.7, 5.0: 10.6, 6.0: 7.7, 7.0: 5.5},
            16.42: {5.0: 10.5, 8.0: 5.15, 10.0: 3.25, 12.0: 2.25},
            23.52: {6.0: 7.5, 10.0: 3.5, 14.0: 1.85, 16.0: 1.1},
            30.62: {8.0: 4.4, 12.0: 2.5, 16.0: 1.35, 20.0: 0.7}
        }
    },
    2.105: {
        "front": max_front_caps,
        "side": {
            9.32:  {3.0: 11.1, 4.0: 6.7, 5.0: 4.55, 6.0: 3.3},
            16.42: {5.0: 4.2, 8.0: 1.9, 10.0: 1.05},
            23.52: {6.0: 2.95, 10.0: 1.25, 12.0: 0.95},
            30.62: {8.0: 1.4, 12.0: 0.9}
        }
    }
}

single_line_pull = 3.5

def get_safe_rad_and_cap(capacities, rad):
    keys = sorted(capacities.keys())
    if rad in keys:
        return rad, capacities[rad]
    if rad < keys[0]:
        return keys[0], capacities[keys[0]]
    if rad > keys[-1]:
        return None, None
        
    for i in range(len(keys) - 1):
        r1, r2 = keys[i], keys[i+1]
        if r1 < rad < r2:
            c1, c2 = capacities[r1], capacities[r2]
            interpolated_cap = c1 + (rad - r1) * (c2 - c1) / (r2 - r1)
            return rad, round(interpolated_cap, 2)
    return None, None

def main(page: ft.Page):
    try:
        page.title = "Kobelco Smart Planner"
        page.scroll = ft.ScrollMode.AUTO
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 15

        # --- အခြေခံ သတ်မှတ်ချက်များ ဝင်စာကွက်များ (ft.DropdownOption သို့ ပြင်ဆင်ပြီး) ---
        outrigger_dd = ft.Dropdown(
            label="Outrigger အကျယ်", 
            options=[ft.DropdownOption(x) for x in ["6.3", "5.9", "5.1", "3.8", "2.105"]], 
            value="6.3"
        )
        area_dd = ft.Dropdown(
            label="မချီမည့် ဧရိယာ", 
            options=[ft.DropdownOption(x) for x in ["360", "front", "side"]], 
            value="360"
        )
        parts_in = ft.TextField(label="ကြိုးအရေအတွက်", value="4", keyboard_type=ft.KeyboardType.NUMBER)

        # --- Auto Planner Component များ ---
        t1_rad = ft.TextField(label="လိုအပ်သော Radius (m)", keyboard_type=ft.KeyboardType.NUMBER)
        t1_load = ft.TextField(label="မချီမည့် ဝန် (တန်)", keyboard_type=ft.KeyboardType.NUMBER)
        t1_res = ft.Text("", size=14, weight=ft.FontWeight.BOLD)

        # --- Manual Check Component များ ---
        t2_boom = ft.Dropdown(
            label="ထုတ်မည့် Boom အရှည် (m)", 
            options=[ft.DropdownOption(x) for x in ["9.32", "16.42", "23.52", "30.62"]], 
            value="16.42"
        )
        t2_rad = ft.TextField(label="အကွာအဝေး Radius (m)", keyboard_type=ft.KeyboardType.NUMBER)
        t2_res = ft.Text("", size=14, weight=ft.FontWeight.BOLD)

        def check_errors():
            area_val = area_dd.value.lower() if area_dd.value else ""
            o_val = outrigger_dd.value
            if o_val == "6.3" and area_val != "360":
                return "⚠️ Outrigger 6.3m တွင် '360' သာ ရွေးပါ။"
            if o_val != "6.3" and area_val == "360":
                return f"⚠️ Outrigger {o_val}m တွင် 'front' သို့မဟုတ် 'side' သာ ရွေးပါ။"
            return None

        def run_tab1(e):
            err = check_errors()
            if err:
                t1_res.value = err
                t1_res.color = "orange"
                page.update()
                return
            try:
                rad_val = float(t1_rad.value)
                load_val = float(t1_load.value)
                rope_cap = int(parts_in.value) * single_line_pull
                booms = crane_database[float(outrigger_dd.value)][area_dd.value.lower()]
                found = False
                res_str = "📊 အလိုအလျောက် တွက်ချက်မှု:\n" + "-"*30 + "\n"
                for b_len, caps in booms.items():
                    if rad_val < b_len:
                        calc_r, chart_c = get_safe_rad_and_cap(caps, rad_val)
                        if calc_r is not None:
                            max_load = min(chart_c, rope_cap)
                            if max_load >= load_val:
                                found = True
                                ang = math.degrees(math.acos(rad_val / b_len))
                                res_str += f"✅ Boom {b_len}m | {ang:.1f}°\n   မနိုင်ဝန်: {max_load} တန်\n\n"
                if not found:
                    t1_res.value = "❌ ဤဝန်အတွက် ချီနိုင်သော Boom မရှိပါ။"
                    t1_res.color = "red"
                else:
                    t1_res.value = res_str
                    t1_res.color = "green"
            except ValueError:
                t1_res.value = "ဂဏန်းများကို မှန်ကန်စွာ ထည့်ပါ။"
                t1_res.color = "red"
            page.update()

        def run_tab2(e):
            err = check_errors()
            if err:
                t2_res.value = err
                t2_res.color = "orange"
                page.update()
                return
            try:
                b_val = float(t2_boom.value)
                r_val = float(t2_rad.value)
                rope_cap = int(parts_in.value) * single_line_pull
                caps = crane_database[float(outrigger_dd.value)][area_dd.value.lower()][b_val]
                
                if r_val >= b_val:
                    t2_res.value = "❌ Radius သည် Boom ထက် မကြီးရပါ။"
                    t2_res.color = "red"
                    page.update()
                    return
                    
                calc_r, chart_c = get_safe_rad_and_cap(caps, r_val)
                if calc_r is None:
                    t2_res.value = "❌ Radius လွန်နေပါသည်။"
                    t2_res.color = "red"
                else:
                    max_load = min(chart_c, rope_cap)
                    ang = math.degrees(math.acos(r_val / b_val))
                    res_text = f"📊 Boom {b_val}m တွက်ချက်မှု:\n" + "-"*30 + f"\n   ထောင့်: {ang:.1f}°\n   မနိုင်ဝန်: {max_load} တန်"
                    t2_res.value = res_text
                    t2_res.color = "green"
            except ValueError:
                t2_res.value = "ဂဏန်းများကို မှန်ကန်စွာ ထည့်ပါ။"
                t2_res.color = "red"
            page.update()

        # --- Layout Views ---
        frame_auto = ft.Column([
            ft.Text("လိုချင်သော Radius နှင့် ဝန်ကို ထည့်ပါ-", italic=True),
            t1_rad, t1_load, 
            ft.ElevatedButton("Boom ရှာမည်", on_click=run_tab1, bgcolor="#0d6efd", color="white"),
            t1_res
        ], visible=True, spacing=10)

        frame_manual = ft.Column([
            ft.Text("ကိုယ်တိုင် Boom ရွေးပြီး တွက်ချက်ပါ-", italic=True),
            t2_boom, t2_rad,
            ft.ElevatedButton("တန်ချိန်တွက်မည်", on_click=run_tab2, bgcolor="#198754", color="white"),
            t2_res
        ], visible=False, spacing=10)

        def show_auto(e):
            btn_auto_tab.bgcolor = "#0d6efd"
            btn_manual_tab.bgcolor = "#6c757d"
            frame_manual.visible = False
            frame_auto.visible = True
            page.update()

        def show_manual(e):
            btn_auto_tab.bgcolor = "#6c757d"
            btn_manual_tab.bgcolor = "#198754"
            frame_auto.visible = False
            frame_manual.visible = True
            page.update()

        btn_auto_tab = ft.ElevatedButton("Auto Planner", on_click=show_auto, bgcolor="#0d6efd", color="white", expand=True)
        btn_manual_tab = ft.ElevatedButton("Manual Check", on_click=show_manual, bgcolor="#6c757d", color="white", expand=True)
        tab_btn_row = ft.Row([btn_auto_tab, btn_manual_tab], spacing=5)

        # 📱 ခေါင်းစဉ်ကို Noti Bar အောက် ရောက်စေရန် Spacer စနစ်
        header = ft.SafeArea(
            content=ft.Column([
                ft.Container(height=15), 
                ft.Text("Kobelco RK250 Lift Planner", size=22, weight=ft.FontWeight.BOLD, color="blue")
            ])
        )

        settings_section = ft.Container(
            content=ft.Column([
                ft.Text("အခြေခံ သတ်မှတ်ချက်များ", weight=ft.FontWeight.BOLD, size=16),
                outrigger_dd, area_dd, parts_in
            ]),
            bgcolor="#f5f5f5",
            padding=10,
            border_radius=8
        )

        page.add(
            header,
            settings_section,
            ft.Divider(),
            tab_btn_row,
            ft.Divider(),
            frame_auto,
            frame_manual
        )
        page.update()

    except Exception as app_error:
        page.controls.clear()
        page.add(
            ft.SafeArea(
                content=ft.Column([
                    ft.Text("⚠️ App Startup Error:", size=20, color="red", weight=ft.FontWeight.BOLD),
                    ft.Text(str(app_error), size=14, color="black"),
                ], spacing=10)
            )
        )
        page.update()

ft.app(target=main)
