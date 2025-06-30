import streamlit as st
import io
import os
from datetime import datetime

# --- 常數定義 ---
PAGE_TITLE = "Kuro家｜貓咪飲食計畫產生器"
PAGE_ICON = "🐈‍"

# --- 輔助函數 ---
def calculate_rer(weight_kg):
    """
    計算貓咪的休息能量需求 (Resting Energy Requirement, RER)。
    公式: RER = 70 * (體重kg ** 0.75)
    """
    if weight_kg <= 0:
        st.error("體重必須大於零。")
        return None
    return 70 * (float(weight_kg)**0.75)

def get_activity_multiplier(age_months, is_neutered, bcs, is_pregnant=False, is_lactating=False):
    """根據貓咪的年齡、絕育狀態、BCS、懷孕/哺乳狀態，返回活動係數。"""
    multiplier = 1.0 # 預設值

    if is_pregnant:
        return 2.0 # 懷孕貓咪
    if is_lactating:
        return 3.0 # 哺乳貓咪 (簡化，可以根據幼貓數量調整)

    if age_months < 4:
        multiplier = 3.0
    elif age_months >= 4 and age_months <= 12:
        multiplier = 2.0
    elif age_months > 12 and age_months < 84: # 假設1到7歲是成貓
        if is_neutered:
            multiplier = 1.2 # 絕育成貓
            if bcs > 5: # 體重過重，目標減肥
                multiplier = 0.8
            elif bcs < 4: # 體重過輕，目標增重
                multiplier = 1.6
        else:
            multiplier = 1.4 # 未絕育成貓
            if bcs > 5: # 體重過重
                multiplier = 1.0
            elif bcs < 4: # 體重過輕
                multiplier = 1.8
    else: # age_months >= 84 (老年貓)
        multiplier = 1.0
        if bcs > 5: # 體重過重
            multiplier = 0.8
        elif bcs < 4: # 體重過輕
            multiplier = 1.2

    return multiplier

def generate_text_report(cat_info, der_info, intake_analysis, monthly_cost_info, feeding_plan): # 調整參數順序
    report_text = f"--- 🐱 貓咪飲食報告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n\n"

    report_text += "📋 貓咪基本資料:\n"
    report_text += f"- 體重: {cat_info.get('weight', 0):.2f} 公斤\n"
    report_text += f"- 年齡: {cat_info.get('age_years', 0)} 歲 {cat_info.get('age_months', 0)} 個月\n"
    report_text += f"- BCS: {cat_info.get('bcs', 0)} / 9\n"
    report_text += f"- 絕育狀態: {cat_info.get('is_neutered', '未知')}\n"
    if cat_info.get('is_pregnant', False):
        report_text += f"- 生理狀態: 懷孕中\n"
    if cat_info.get('is_lactating', False):
        report_text += f"- 生理狀態: 哺乳中\n"
    report_text += "--------------------------------------\n\n"

    report_text += "📈 每日建議攝取:\n"
    report_text += f"- 建議熱量 (DER): {der_info.get('der', 0):.2f} 大卡/天\n"
    report_text += "--------------------------------------\n\n"

    if intake_analysis:
        report_text += "📊 目前飲食分析:\n"
        report_text += f"- 從乾乾攝取的熱量: {intake_analysis.get('dry_food_kcal', 0):.2f} 大卡\n"
        report_text += f"- 從濕食攝取的熱量: {intake_analysis.get('wet_food_kcal', 0):.2f} 大卡\n"
        report_text += f"- 每日總攝取熱量: {intake_analysis.get('total_intake', 0):.2f} 大卡\n"
        diff = intake_analysis.get('calorie_difference', 0)
        report_text += f"- 與建議量差異: {diff:+.2f} 大卡\n"
        if diff > 5:
            report_text += "(攝取超標，建議調整)\n"
        elif diff < -5:
            report_text += "(攝取不足，建議調整)\n"
        else:
            report_text += "(熱量攝取接近建議值)\n"
        report_text += "--------------------------------------\n\n"
    else:
        report_text += "📊 目前飲食分析: 尚未輸入餵食資訊，無法分析。\n"
        report_text += "--------------------------------------\n\n"
    
    # 將伙食費顯示在飲食分析後面
    if monthly_cost_info and monthly_cost_info.get('total_monthly_cost') is not None:
        report_text += "💰 目前每月伙食費:\n" # 修改標題
        report_text += f"- 每日乾食花費: {monthly_cost_info.get('daily_dry_cost', 0):.2f} 元\n"
        report_text += f"- 每日濕食花費: {monthly_cost_info.get('daily_wet_cost', 0):.2f} 元\n"
        report_text += f"- 每月總伙食費: {monthly_cost_info.get('total_monthly_cost', 0):.2f} 元 (以30天計)\n"
        report_text += "--------------------------------------\n\n"
    else:
        report_text += "💰 目前每月伙食費: 尚未輸入食物價格資訊，無法估算。\n" # 修改標題
        report_text += "--------------------------------------\n\n"

    if feeding_plan and feeding_plan.get('target_kcal') is not None:
        report_text += "🥗 建議餵食計畫:\n"
        report_text += f"目標熱量約: {feeding_plan.get('target_kcal', 0):.0f} 大卡/天\n"
        report_text += f"熱量佔比: {100 - feeding_plan.get('wet_food_percentage', 0)}% 乾食 / {feeding_plan.get('wet_food_percentage', 0)}% 濕食\n"
        report_text += f"- 建議乾食餵食量: {feeding_plan.get('required_dry_grams', 0):.1f} 公克/天\n"
        report_text += f"- 建議濕食餵食量: {feeding_plan.get('required_wet_grams', 0):.1f} 公克/天\n"
        report_text += "--------------------------------------\n\n"
    else:
        report_text += "🥗 建議餵食計畫: 尚未計算或無有效食物熱量資訊。\n"
        report_text += "--------------------------------------\n\n"
    
    report_text += "ℹ️ 免責聲明與重要提示：\n"
    report_text += """
此工具提供的熱量需求為估算值，基於常用公式和參考數據。
每隻貓咪的代謝、活動量、健康狀況、品種及個別差異都可能影響實際熱量需求。
在任何飲食調整（特別是增重或減重計畫）前，請務必諮詢您的獸醫或專業寵物營養師，
獲取最精確的建議與指導，以確保貓咪的健康與安全。
本工具不提供醫療診斷或治療建議。
"""
    report_text += "\n--------------------------------------"
    report_text += "\nKuro家｜貓咪飲食計畫產生器 (僅供參考)"

    return report_text

# --- 主要應用程式邏輯 ---
def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
    st.title(f"{PAGE_ICON} {PAGE_TITLE}")

    # 初始化 session_state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    # 初始化所有可能需要跨步驟存儲的變量
    if 'der' not in st.session_state: st.session_state.der = None
    if 'cat_info' not in st.session_state: st.session_state.cat_info = {}
    if 'der_info' not in st.session_state: st.session_state.der_info = {}
    if 'intake_analysis' not in st.session_state: st.session_state.intake_analysis = None
    if 'feeding_plan' not in st.session_state: st.session_state.feeding_plan = None
    if 'monthly_cost_info' not in st.session_state: st.session_state.monthly_cost_info = None
    
    # 預設值，確保每次頁面重載時都有值
    if 'dry_food_grams' not in st.session_state: st.session_state.dry_food_grams = 0.0
    if 'wet_food_grams' not in st.session_state: st.session_state.wet_food_grams = 0.0
    if 'dry_food_kcal_per_1000g' not in st.session_state: st.session_state.dry_food_kcal_per_1000g = 3600.0
    if 'wet_food_kcal_per_100g' not in st.session_state: st.session_state.wet_food_kcal_per_100g = 100.0
    if 'dry_food_package_weight' not in st.session_state: st.session_state.dry_food_package_weight = 1500.0
    if 'dry_food_package_price' not in st.session_state: st.session_state.dry_food_package_price = 800.0
    if 'wet_food_package_weight' not in st.session_state: st.session_state.wet_food_package_weight = 80.0
    if 'wet_food_package_price' not in st.session_state: st.session_state.wet_food_package_price = 50.0
    if 'wet_food_percentage_plan' not in st.session_state: st.session_state.wet_food_percentage_plan = 50

    # --- 步驟 1: 計算建議熱量 ---
    if st.session_state.current_step == 1:
        st.header("🐾 第一步：計算建議熱量")
        st.info("請輸入貓咪的詳細基本資料，以估算其每日所需的熱量。")

        # 使用 session_state 中的值作為預設值
        weight_s1 = st.number_input("體重 (公斤)", min_value=0.1, max_value=20.0, value=st.session_state.cat_info.get('weight', 4.0), step=0.1, key="weight_s1")
        age_years_s1 = st.number_input("年齡 (歲)", min_value=0, max_value=25, value=st.session_state.cat_info.get('age_years', 2), step=1, key="age_years_s1")
        age_months_s1 = st.number_input("年齡 (個月)", min_value=0, max_value=11, value=st.session_state.cat_info.get('age_months', 0), step=1, key="age_months_s1")
        
        is_neutered_s1_options = ('是', '否')
        is_neutered_s1_index = is_neutered_s1_options.index(st.session_state.cat_info.get('is_neutered', '是'))
        is_neutered_s1_display = st.radio("是否已絕育？", is_neutered_s1_options, index=is_neutered_s1_index, key="is_neutered_s1")
        is_neutered_s1 = (is_neutered_s1_display == '是')
        
        bcs_s1 = st.slider("身體狀況評分 BCS (1:過瘦, 5:理想, 9:過胖)", min_value=1, max_value=9, value=st.session_state.cat_info.get('bcs', 5), key="bcs_s1")
        st.caption("""
        - **1-3分 (過瘦):** 肋骨、脊椎易見且突出。
        - **4-5分 (理想):** 肋骨可觸及，腰身明顯。
        - **6-7分 (過重):** 肋骨不易觸及，腰身不明顯。
        - **8-9分 (肥胖):** 肋骨難以觸及，腹部明顯下垂。
        """)
        is_pregnant_s1 = st.checkbox("母貓是否懷孕？", value=st.session_state.cat_info.get('is_pregnant', False), key="is_pregnant_s1")
        is_lactating_s1 = st.checkbox("母貓是否哺乳中？", value=st.session_state.cat_info.get('is_lactating', False), key="is_lactating_s1")
        
        st.markdown("---")
        
        # 步驟1的「計算」按鈕
        if st.button("✅ 計算貓咪每日所需熱量", key="calc_der_s1_btn"):
            age = age_years_s1 * 12 + age_months_s1

            if age <= 0:
                st.error("貓咪總年齡必須大於 0 個月，請重新輸入。")
            else:
                rer = calculate_rer(weight_s1)
                if rer is not None:
                    multiplier = get_activity_multiplier(age, is_neutered_s1, bcs_s1, is_pregnant_s1, is_lactating_s1)
                    der = rer * multiplier
                    st.session_state.der = der

                    # 將輸入值保存到 session_state，供下次加載或報告使用
                    st.session_state.cat_info = {
                        "weight": weight_s1, "age_years": age_years_s1, "age_months": age_months_s1,
                        "is_neutered": is_neutered_s1_display, "is_neutered_bool": is_neutered_s1,
                        "bcs": bcs_s1, "is_pregnant": is_pregnant_s1, "is_lactating": is_lactating_s1
                    }
                    st.session_state.der_info = {
                        "rer": rer, "multiplier": multiplier, "der": der
                    }

                    st.subheader("📈 計算結果")
                    st.write(f"靜息能量需求 (RER): **{rer:.2f} 大卡/天**")
                    st.write(f"活動係數: **{multiplier:.1f}**")
                    st.success(f"每日建議熱量 (DER): **{der:.2f} 大卡/天**")
                    st.info("DER 是根據貓咪的詳細身體狀況估算的每日建議攝取熱量。")
        
        # 只有在DER計算成功後才顯示「下一步」按鈕
        if st.session_state.der is not None:
            st.markdown("---")
            if st.button("➡️ 進入第二步：分析目前飲食", key="next_step1_btn"):
                st.session_state.current_step = 2
                st.rerun()

    # --- 步驟 2: 分析目前飲食 ---
    elif st.session_state.current_step == 2:
        st.header("📊 第二步：分析目前飲食")
        st.info("請輸入貓咪目前每日的餵食量、食物熱量與價格資訊。")

        # 返回上一步按鈕
        if st.button("◀️ 返回第一步", key="back_to_step1"):
            st.session_state.current_step = 1
            st.rerun()
        
        st.markdown("---") # 分隔線
        
        st.subheader("乾食 (乾乾) 資訊")
        # 使用 session_state 中的值作為預設值
        dry_food_grams_s2 = st.number_input("每日總餵食量 (公克)", key="dry_grams_s2", min_value=0.0, step=1.0, value=st.session_state.dry_food_grams)
        dry_food_kcal_per_1000g_s2 = st.number_input("每 1000 公克的熱量 (大卡)", key="dry_kcal_s2", min_value=0.0, value=st.session_state.dry_food_kcal_per_1000g, step=10.0)
        dry_food_package_weight_s2 = st.number_input("每包乾食重量 (公克)", key="dry_package_weight_s2", min_value=0.0, value=st.session_state.dry_food_package_weight, step=10.0)
        dry_food_package_price_s2 = st.number_input("每包乾食價格 (元)", key="dry_package_price_s2", min_value=0.0, value=st.session_state.dry_food_package_price, step=1.0)

        st.subheader("濕食 (主食罐/副食罐) 資訊")
        # 使用 session_state 中的值作為預設值
        wet_food_grams_s2 = st.number_input("每日總餵食量 (公克)", key="wet_grams_s2", min_value=0.0, step=1.0, value=st.session_state.wet_food_grams)
        wet_food_kcal_per_100g_s2 = st.number_input("每 100 公克的熱量 (大卡)", key="wet_kcal_s2", min_value=0.0, value=st.session_state.wet_food_kcal_per_100g, step=1.0)
        wet_food_package_weight_s2 = st.number_input("每罐/包濕食重量 (公克)", key="wet_package_weight_s2", min_value=0.0, value=st.session_state.wet_food_package_weight, step=1.0)
        wet_food_package_price_s2 = st.number_input("每罐/包濕食價格 (元)", key="wet_package_price_s2", min_value=0.0, value=st.session_state.wet_food_package_price, step=1.0)

        st.markdown("---")
        
        # 步驟2的「計算」按鈕
        if st.button("✅ 計算實際攝取與費用", key="analyze_intake_s2_btn"):
            if st.session_state.der is None:
                st.error("⚠️ 請先返回第一步，完成每日建議熱量的計算！")
            elif dry_food_kcal_per_1000g_s2 == 0 and wet_food_kcal_per_100g_s2 == 0:
                st.warning("⚠️ 請輸入至少一種食物的熱量資訊，才能進行分析。")
            else:
                # 將輸入值保存到 session_state
                st.session_state.dry_food_grams = dry_food_grams_s2
                st.session_state.wet_food_grams = wet_food_grams_s2
                st.session_state.dry_food_kcal_per_1000g = dry_food_kcal_per_1000g_s2
                st.session_state.wet_food_kcal_per_100g = wet_food_kcal_per_100g_s2
                st.session_state.dry_food_package_weight = dry_food_package_weight_s2
                st.session_state.dry_food_package_price = dry_food_package_price_s2
                st.session_state.wet_food_package_weight = wet_food_package_weight_s2
                st.session_state.wet_food_package_price = wet_food_package_price_s2

                der = st.session_state.der
                dry_food_calories = (dry_food_grams_s2 / 1000.0) * dry_food_kcal_per_1000g_s2
                wet_food_calories = (wet_food_grams_s2 / 100.0) * wet_food_kcal_per_100g_s2
                total_intake = dry_food_calories + wet_food_calories
                calorie_difference = total_intake - der

                st.session_state.intake_analysis = {
                    "dry_food_grams": dry_food_grams_s2, "dry_food_kcal": dry_food_calories,
                    "wet_food_grams": wet_food_grams_s2, "wet_food_kcal": wet_food_calories,
                    "total_intake": total_intake, "calorie_difference": calorie_difference
                }
                
                # 計算伙食費
                daily_dry_cost = 0.0
                if dry_food_package_weight_s2 > 0:
                    cost_per_gram_dry = dry_food_package_price_s2 / dry_food_package_weight_s2
                    daily_dry_cost = dry_food_grams_s2 * cost_per_gram_dry
                
                daily_wet_cost = 0.0
                if wet_food_package_weight_s2 > 0:
                    cost_per_gram_wet = wet_food_package_price_s2 / wet_food_package_weight_s2
                    daily_wet_cost = wet_food_grams_s2 * cost_per_gram_wet
                
                total_daily_cost = daily_dry_cost + daily_wet_cost
                total_monthly_cost = total_daily_cost * 30 # 以30天計算每月

                st.session_state.monthly_cost_info = {
                    "daily_dry_cost": daily_dry_cost,
                    "daily_wet_cost": daily_wet_cost,
                    "total_daily_cost": total_daily_cost,
                    "total_monthly_cost": total_monthly_cost
                }
                
                # 顯示當前分析結果
                st.subheader("📊 熱量攝取分析")
                st.write(f"從乾乾攝取的熱量: **{dry_food_calories:.2f} 大卡**")
                st.write(f"從濕食攝取的熱量: **{wet_food_calories:.2f} 大卡**")
                st.success(f"貓咪每日總攝取熱量: **{total_intake:.2f} 大卡**")

                st.markdown("---")
                st.subheader("⚖️ 攝取與建議量比較")
                st.write(f"每日建議攝取 (DER): **{der:.2f} 大卡**")
                st.write(f"每日實際攝取: **{total_intake:.2f} 大卡**")

                if calorie_difference > 5:
                    st.warning(f"❗️ **攝取超標**：比建議值多了 **{calorie_difference:.2f} 大卡**。")
                    st.info("提醒：長期熱量超標可能導致肥胖及相關健康問題，請考慮與獸醫師討論並調整餵食量。")
                elif calorie_difference < -5:
                    st.warning(f"❗️ **攝取不足**：比建議值少了 **{-calorie_difference:.2f} 大卡**。")
                    st.info("提醒：長期熱量不足可能影響貓咪健康與活力，請確認是否需要增加餵食量或更換更高熱量的食物。")
                else:
                    st.balloons()
                    st.success("🎉 **完美！** 貓咪的熱量攝取與建議值非常接近！")
                
                st.markdown("---")
                st.subheader("💰 目前每月伙食費") # 修改標題
                col_cost1, col_cost2 = st.columns(2)
                col_cost1.metric("每日總花費", f"{total_daily_cost:.2f} 元")
                col_cost2.metric("每月總花費", f"{total_monthly_cost:.2f} 元")
                st.caption("此為根據您輸入的食物價格和每日餵食量估算，以30天計。")
        
        # 只有在分析完成後才顯示「下一步」按鈕
        if st.session_state.intake_analysis is not None:
            st.markdown("---")
            if st.button("➡️ 進入第三步：規劃飲食建議", key="next_step2_btn"):
                st.session_state.current_step = 3
                st.rerun()


    # --- 步驟 3: 規劃飲食建議 ---
    elif st.session_state.current_step == 3:
        st.header("🥗 第三步：規劃飲食建議")
        st.info("根據建議熱量，規劃理想的乾濕食比例與餵食量。")

        # 返回上一步按鈕
        if st.button("◀️ 返回第二步", key="back_to_step2"):
            st.session_state.current_step = 2
            st.rerun()

        st.markdown("---") # 分隔線

        if st.session_state.der is None:
            st.warning("⚠️ 請先返回第一步，完成貓咪的每日建議熱量 (DER) 計算。")
        elif st.session_state.dry_food_kcal_per_1000g == 0 and st.session_state.wet_food_kcal_per_100g == 0:
            st.warning("⚠️ 請返回第二步，輸入至少一種食物的熱量資訊，才能進行餵食量建議。")
        else:
            st.subheader("設定乾濕食熱量比例")
            wet_food_percentage_s3 = st.slider(
                "希望「濕食」提供的熱量佔每日總熱量的百分比 (%)",
                min_value=0, max_value=100, value=st.session_state.wet_food_percentage_plan, step=5, key="wet_food_percentage_s3"
            )
            st.session_state.wet_food_percentage_plan = wet_food_percentage_s3 # 保存值

            st.markdown("---")
            # 步驟3的「計算」按鈕
            if st.button("✅ 產生建議餵食量", key="generate_plan_s3_btn"):
                der = st.session_state.der
                target_wet_calories = der * (wet_food_percentage_s3 / 100.0)
                target_dry_calories = der * ((100 - wet_food_percentage_s3) / 100.0)

                required_dry_grams = 0.0
                if st.session_state.dry_food_kcal_per_1000g > 0:
                    required_dry_grams = (target_dry_calories / st.session_state.dry_food_kcal_per_1000g) * 1000.0
                
                required_wet_grams = 0.0
                if st.session_state.wet_food_kcal_per_100g > 0:
                    required_wet_grams = (target_wet_calories / st.session_state.wet_food_kcal_per_100g) * 100.0

                st.session_state.feeding_plan = {
                    "wet_food_percentage": wet_food_percentage_s3,
                    "required_dry_grams": required_dry_grams,
                    "required_wet_grams": required_wet_grams,
                    "target_kcal": der
                }

                # 顯示當前計畫結果
                st.subheader("🍽️ 每日建議餵食量")
                st.info(f"為了達到每日 **{der:.2f} 大卡** 的目標：")
                
                col_rec_1, col_rec_2 = st.columns(2)
                with col_rec_1:
                    st.metric(label="乾食 (乾乾)", value=f"{required_dry_grams:.1f} 公克")
                with col_rec_2:
                    st.metric(label="濕食 (主食罐)", value=f"{required_wet_grams:.1f} 公克")

                st.caption(f"此建議是基於 {100-wet_food_percentage_s3}% 乾食與 {wet_food_percentage_s3}% 濕食的熱量佔比所計算。請在 1-2 週內密切觀察貓咪的體重和身體狀況，並與您的獸醫師討論，視情況微調餵食量。")
        
        # 只有在計畫生成後才顯示「下一步」按鈕
        if st.session_state.feeding_plan is not None:
            st.markdown("---")
            if st.button("➡️ 進入第四步：飲食報告總覽", key="next_step3_btn"):
                st.session_state.current_step = 4
                st.rerun()


    # --- 步驟 4: 飲食報告總覽 ---
    elif st.session_state.current_step == 4:
        st.header("📄 第四步：飲食報告總覽")
        st.info("這是為您的貓咪生成的完整飲食報告。")

        # 返回上一步按鈕
        if st.button("◀️ 返回第三步", key="back_to_step3"):
            st.session_state.current_step = 3
            st.rerun()

        st.markdown("---") # 分隔線

        # 檢查所有必要數據是否存在，否則提示用戶從頭開始
        if (st.session_state.der_info.get('der') is None or
            st.session_state.intake_analysis is None or
            st.session_state.feeding_plan is None or
            st.session_state.monthly_cost_info is None):
            st.warning("⚠️ 報告生成所需資訊不完整。請返回第一步開始填寫所有資訊。")
        else:
            cat_info = st.session_state.get('cat_info', {})
            der_info = st.session_state.get('der_info', {})
            intake_analysis = st.session_state.get('intake_analysis')
            feeding_plan = st.session_state.get('feeding_plan')
            monthly_cost_info = st.session_state.get('monthly_cost_info')

            st.subheader("🐾 貓咪基本資料")
            col1, col2 = st.columns(2)
            col1.metric("體重", f"{cat_info.get('weight', 0):.2f} 公斤")
            col1.metric("BCS", f"{cat_info.get('bcs', 0)} / 9")
            col2.metric("年齡", f"{cat_info.get('age_years', 0)} 歲 {cat_info.get('age_months', 0)} 個月")
            col2.metric("絕育狀態", cat_info.get('is_neutered', '未知'))
            if cat_info.get('is_pregnant', False) or cat_info.get('is_lactating', False):
                special_status = []
                if cat_info.get('is_pregnant', False): special_status.append("懷孕")
                if cat_info.get('is_lactating', False): special_status.append("哺乳")
                st.write(f"**特殊生理狀態**: {', '.join(special_status)}")
            st.markdown("---")

            st.subheader("📈 每日建議攝取")
            st.metric("建議熱量 (DER)", f"{der_info.get('der', 0):.2f} 大卡/天")
            st.markdown("---")

            st.subheader("📊 目前飲食分析")
            col1, col2 = st.columns(2)
            col1.metric("每日總攝取熱量", f"{intake_analysis.get('total_intake', 0):.2f} 大卡")
            diff = intake_analysis.get('calorie_difference', 0)
            if diff > 5:
                delta_text = f"+{diff:.2f} 大卡"
                delta_color = "inverse"
            elif diff < -5:
                delta_text = f"{diff:.2f} 大卡"
                delta_color = "off"
            else:
                delta_text = "接近理想"
                delta_color = "normal"
            col2.metric("與建議量差異", f"{diff:+.2f} 大卡", delta=delta_text, delta_color=delta_color)
            st.markdown("---")

            # 將伙食費顯示在飲食分析後面
            if monthly_cost_info:
                st.subheader("💰 目前每月伙食費") # 修改標題
                col1, col2 = st.columns(2)
                col1.metric("每日總花費", f"{monthly_cost_info.get('total_daily_cost', 0):.2f} 元")
                col2.metric("每月總花費", f"{monthly_cost_info.get('total_monthly_cost', 0):.2f} 元")
                st.caption("此為根據您輸入的食物價格和每日餵食量估算，以30天計。")
                st.markdown("---")

            st.subheader("🥗 建議餵食計畫")
            st.write(f"基於 **{100 - feeding_plan.get('wet_food_percentage', 0)}% 乾食** 與 **{feeding_plan.get('wet_food_percentage', 0)}% 濕食** 的熱量佔比，目標約 **{feeding_plan.get('target_kcal', 0):.0f} 大卡/天**")
            col1, col2 = st.columns(2)
            col1.metric("建議乾食餵食量", f"{feeding_plan.get('required_dry_grams', 0):.1f} 公克/天")
            col2.metric("建議濕食餵食量", f"{feeding_plan.get('required_wet_grams', 0):.1f} 公克/天")
            st.caption("此為粗略建議，請諮詢獸醫獲取精確處方糧或食譜。")
            st.markdown("---")
            
            st.subheader("📄 一鍵複製飲食報告")
            
            # 調整 generate_text_report 的參數順序
            full_report_text = generate_text_report(cat_info, der_info, intake_analysis, monthly_cost_info, feeding_plan)
            
            st.code(full_report_text, language="text")            
            st.info("💡 點擊上方報告內容區塊右上角的複製按鈕，即可將報告內容複製到剪貼簿。")
            
            st.markdown("---")
            # 重設按鈕
            if st.button("🔄 重新開始計算", key="reset_app"):
                st.session_state.current_step = 1
                # 清除所有相關的 session_state 數據
                for key in ['der', 'cat_info', 'der_info', 'intake_analysis', 'feeding_plan', 'monthly_cost_info',
                            'dry_food_grams', 'wet_food_grams',
                            'dry_food_kcal_per_1000g', 'wet_food_kcal_per_100g',
                            'dry_food_package_weight', 'dry_food_package_price',
                            'wet_food_package_weight', 'wet_food_package_price',
                            'wet_food_percentage_plan']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()


if __name__ == "__main__":
    main()