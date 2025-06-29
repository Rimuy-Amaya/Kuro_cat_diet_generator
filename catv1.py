import streamlit as st

def calculate_rer(weight_kg):
    """
    計算貓咪的休息能量需求 (Resting Energy Requirement, RER)。
    公式: RER = 70 * (體重kg ** 0.75)
    """
    if weight_kg <= 0:
        # 在 Streamlit 中，顯示錯誤訊息比拋出異常更友好
        st.error("體重必須大於零。")
        return None
    # 使用 0.75 次方，確保是浮點數結果
    return 70 * (float(weight_kg)**0.75)

def get_activity_multiplier(age_months, is_neutered, bcs, is_pregnant=False, is_lactating=False):
    """根據貓咪的年齡、絕育狀態、BCS、懷孕/哺乳狀態，返回活動係數。"""
    multiplier = 1.0 # 預設值

    if is_pregnant:
        return 2.0 # 懷孕貓咪
    if is_lactating:
        return 3.0 # 哺乳貓咪 (簡化，可以根據幼貓數量調整)

    # 幼貓
    if age_months < 4:
        multiplier = 3.0
    elif age_months >= 4 and age_months <= 12:
        multiplier = 2.0
    # 成貓 (1歲以上)
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
    # 老年貓 (7歲以上)
    else: # age_months >= 84
        multiplier = 1.0 # 老年貓
        if bcs > 5: # 體重過重
            multiplier = 0.8
        elif bcs < 4: # 體重過輕
            multiplier = 1.2

    return multiplier

def main():
    """
    Streamlit 應用程式主體。
    """
    st.set_page_config(page_title="Kuro家貓咪熱量計算機", page_icon="🐈‍")
    st.title("🐈‍ Kuro家貓咪熱量計算機")

    # 使用 st.tabs 將流程分為清晰的三個步驟，優化使用者介面
    tab1, tab2, tab3 = st.tabs([
        "🐾 **第一步：計算建議熱量**",
        "📊 **第二步：分析目前飲食**",
        "🥗 **第三步：規劃飲食建議**"
    ])

    # --- Tab 1: 計算建議熱量 (DER) ---
    with tab1:
        st.subheader("輸入貓咪基本資料")
        col_a, col_b = st.columns(2)
        with col_a:
            weight = st.number_input("體重 (公斤)", min_value=0.1, max_value=20.0, value=4.0, step=0.1)
            age = st.number_input("年齡 (月)", min_value=1, max_value=300, value=24, step=1)
            is_neutered = st.radio("是否已絕育？", ('是', '否')) == '是'
        with col_b:
            bcs = st.slider("身體狀況評分 BCS (1:過瘦, 5:理想, 9:過胖)", min_value=1, max_value=9, value=5)
            is_pregnant = st.checkbox("母貓是否懷孕？")
            is_lactating = st.checkbox("母貓是否哺乳中？")
        
        # --- 計算按鈕 ---
        if st.button("✅ 計算貓咪每日所需熱量", key="calc_der"):
            # 將計算結果保存在 session state 中，以便第二部分使用
            rer = calculate_rer(weight)
            if rer is not None:
                multiplier = get_activity_multiplier(age, is_neutered, bcs, is_pregnant, is_lactating)
                der = rer * multiplier
                st.session_state.der = der # 將 der 存儲在 session state
                st.subheader("📈 計算結果")
                st.write(f"靜息能量需求 (RER): **{rer:.2f} 大卡/天**")
                st.write(f"活動係數: **{multiplier:.1f}**")
                st.success(f"每日建議熱量 (DER): **{der:.2f} 大卡/天**")
                st.info("DER 是根據貓咪的詳細身體狀況估算的每日建議攝取熱量。")

    # --- Tab 2: 計算實際攝取熱量並比較 ---
    with tab2:
        st.subheader("輸入目前每日餵食資訊")
        st.caption("請輸入貓咪目前正在吃的食物資訊，以計算每日總攝取熱量。")

        # --- 乾食輸入 ---
        st.subheader("乾食 (乾乾)")
        col1, col2 = st.columns(2)
        with col1:
            dry_food_grams = st.number_input("每日總餵食量 (公克)", key="dry_grams", min_value=0.0, step=1.0)
        with col2:
            dry_food_kcal_per_1000g = st.number_input("每 1000 公克的熱量 (大卡)", key="dry_kcal", min_value=0.0, step=10.0)

        # --- 濕食輸入 ---
        st.subheader("濕食 (主食罐/副食罐)")
        col3, col4 = st.columns(2)
        with col3:
            wet_food_grams = st.number_input("每日總餵食量 (公克)", key="wet_grams", min_value=0.0, step=1.0)
        with col4:
            wet_food_kcal_per_100g = st.number_input("每 100 公克的熱量 (大卡)", key="wet_kcal", min_value=0.0, step=1.0)

        # --- 計算與比較按鈕 ---
        if st.button("✅ 計算實際攝取並比較", key="analyze_intake"):
            # 檢查第一步是否已成功計算出 DER
            if 'der' not in st.session_state or st.session_state.der is None:
                st.error("請先在第一步完成每日建議熱量的計算！")
                st.stop()

            der = st.session_state.der
            # 根據 prompt 需求計算熱量
            dry_food_calories = (dry_food_grams / 1000.0) * dry_food_kcal_per_1000g
            wet_food_calories = (wet_food_grams / 100.0) * wet_food_kcal_per_100g
            total_intake = dry_food_calories + wet_food_calories

            st.subheader("📊 熱量攝取分析")
            st.write(f"從乾乾攝取的熱量: **{dry_food_calories:.2f} 大卡**")
            st.write(f"從濕食攝取的熱量: **{wet_food_calories:.2f} 大卡**")
            st.success(f"貓咪每日總攝取熱量: **{total_intake:.2f} 大卡**")

            # 進行比較
            st.markdown("---")
            st.subheader("⚖️ 攝取與建議量比較")
            
            calorie_difference = total_intake - der
            
            st.write(f"每日建議攝取 (DER): **{der:.2f} 大卡**")
            st.write(f"每日實際攝取: **{total_intake:.2f} 大卡**")

            if calorie_difference > 5: # 給予一個小小的緩衝範圍
                st.warning(f"❗️ **攝取超標**：比建議值多了 **{calorie_difference:.2f} 大卡**。")
                st.info("提醒：長期熱量超標可能導致肥胖及相關健康問題，請考慮與獸醫師討論並調整餵食量。")
            elif calorie_difference < -5:
                st.warning(f"❗️ **攝取不足**：比建議值少了 **{-calorie_difference:.2f} 大卡**。")
                st.info("提醒：長期熱量不足可能影響貓咪健康與活力，請確認是否需要增加餵食量或更換更高熱量的食物。")
            else:
                st.balloons()
                st.success("🎉 **完美！** 貓咪的熱量攝取與建議值非常接近！")

    # --- Tab 3: 飲食調整建議 ---
    with tab3:
        st.subheader("規劃理想的乾濕食餵食量")
        st.info("此功能會根據第一步計算出的「每日建議熱量 (DER)」來產生新的飲食計畫。")

        # 檢查是否已完成第一步和第二步的必要輸入
        if 'der' not in st.session_state or st.session_state.der is None:
            st.warning("請先在第一步計算貓咪的每日建議熱量 (DER)。")
        # 為了計算克數，必須要有食物熱量資訊。我們從第二步的輸入框獲取。
        elif dry_food_kcal_per_1000g == 0 and wet_food_kcal_per_100g == 0:
            st.warning("請在第二步輸入至少一種食物的熱量資訊，才能進行餵食量建議。")
        else:
            # 讓使用者設定乾濕食的熱量比例
            st.subheader("設定乾濕食熱量比例")
            wet_food_percentage = st.slider(
                "希望「濕食」提供的熱量佔每日總熱量的百分比 (%)",
                min_value=0, max_value=100, value=50, step=5
            )

            if st.button("⚖️ 產生建議餵食量", key="generate_plan"):
                der = st.session_state.der
                target_wet_calories = der * (wet_food_percentage / 100.0)
                target_dry_calories = der * ((100 - wet_food_percentage) / 100.0)

                # 計算建議的公克數
                required_dry_grams = (target_dry_calories / dry_food_kcal_per_1000g) * 1000.0 if dry_food_kcal_per_1000g > 0 else 0
                required_wet_grams = (target_wet_calories / wet_food_kcal_per_100g) * 100.0 if wet_food_kcal_per_100g > 0 else 0

                st.subheader("🍽️ 每日建議餵食量")
                st.info(f"為了達到每日 **{der:.2f} 大卡** 的目標：")

                col_rec_1, col_rec_2 = st.columns(2)
                with col_rec_1:
                    st.metric(label="乾食 (乾乾)", value=f"{required_dry_grams:.1f} 公克")
                with col_rec_2:
                    st.metric(label="濕食 (主食罐)", value=f"{required_wet_grams:.1f} 公克")

                st.caption(f"此建議是基於 {100-wet_food_percentage}% 乾食與 {wet_food_percentage}% 濕食的熱量佔比所計算。請在 1-2 週內密切觀察貓咪的體重和身體狀況，並與您的獸醫師討論，視情況微調餵食量。")

if __name__ == "__main__":
    main()
