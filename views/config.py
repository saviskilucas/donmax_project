import streamlit as st

def render():
    st.markdown("<div class='section-header'>⚙️ CONFIGURAÇÕES DO SISTEMA</div>", unsafe_allow_html=True)
    st.markdown("**Don Max Buffet v1.0**\n*Sistema Integrado de Controle de Pesagens*\n\n---\n\n**Instruções para a Cozinha:**\n1. Realize as pesagens sempre ao final do turno.\n2. Certifique-se de zerar a tara da balança.\n3. Dúvidas ou problemas falar com a gerência.")
    
    if st.button("🔄 Limpar Cache Geral"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache limpo com sucesso!")