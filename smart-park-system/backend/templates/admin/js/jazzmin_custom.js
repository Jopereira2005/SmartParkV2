// ============================================================================
// SmartPark - Jazzmin Custom JavaScript
// ============================================================================

document.addEventListener("DOMContentLoaded", function () {
  // Adicionar tooltips aos elementos que têm título
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll("[title]")
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    // Usando Bootstrap tooltips se disponível
    if (typeof bootstrap !== "undefined" && bootstrap.Tooltip) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    }
  });

  // Adicionar confirmação para ações perigosas
  const dangerButtons = document.querySelectorAll(".btn-danger, .deletelink");
  dangerButtons.forEach(function (button) {
    button.addEventListener("click", function (e) {
      const confirmMessage =
        "Tem certeza que deseja realizar esta ação? Esta operação não pode ser desfeita.";
      if (!confirm(confirmMessage)) {
        e.preventDefault();
        return false;
      }
    });
  });

  // Melhorar UX dos formulários com feedback visual
  const formInputs = document.querySelectorAll("input, select, textarea");
  formInputs.forEach(function (input) {
    input.addEventListener("focus", function () {
      this.parentElement.classList.add("focused");
    });

    input.addEventListener("blur", function () {
      this.parentElement.classList.remove("focused");
      if (this.value) {
        this.parentElement.classList.add("has-value");
      } else {
        this.parentElement.classList.remove("has-value");
      }
    });

    // Adicionar classe se já tem valor
    if (input.value) {
      input.parentElement.classList.add("has-value");
    }
  });

  // Auto-refresh para páginas de monitoramento (como dashboard)
  if (
    window.location.pathname.includes("/admin/") &&
    (window.location.pathname.endsWith("/admin/") ||
      window.location.pathname.includes("changelist"))
  ) {
    // Adicionar botão de refresh manual
    const refreshButton = document.createElement("button");
    refreshButton.innerHTML = '<i class="fas fa-sync-alt"></i> Atualizar';
    refreshButton.className = "btn btn-sm btn-outline-primary ml-2";
    refreshButton.type = "button";
    refreshButton.onclick = function () {
      window.location.reload();
    };

    const toolbar =
      document.querySelector(".object-tools") ||
      document.querySelector(".toolbar") ||
      document.querySelector(".breadcrumb");

    if (toolbar) {
      toolbar.appendChild(refreshButton);
    }
  }

  // Adicionar timestamps nas páginas de listagem
  const timestamps = document.querySelectorAll(".datetime");
  timestamps.forEach(function (timestamp) {
    const date = new Date(timestamp.textContent);
    if (!isNaN(date.getTime())) {
      const now = new Date();
      const diff = now - date;
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor(diff / (1000 * 60));

      let relativeTime = "";
      if (days > 0) {
        relativeTime = `${days} dia(s) atrás`;
      } else if (hours > 0) {
        relativeTime = `${hours} hora(s) atrás`;
      } else if (minutes > 0) {
        relativeTime = `${minutes} minuto(s) atrás`;
      } else {
        relativeTime = "Agora mesmo";
      }

      timestamp.title = `${timestamp.textContent} (${relativeTime})`;
    }
  });

  // Adicionar indicadores de status com cores
  const statusElements = document.querySelectorAll(
    ".field-status, .field-state, .field-onboarding_status"
  );
  statusElements.forEach(function (element) {
    const text = element.textContent.toLowerCase().trim();

    if (
      text.includes("ativo") ||
      text.includes("active") ||
      text.includes("online")
    ) {
      element.classList.add("status-active");
      element.innerHTML =
        '<i class="fas fa-circle text-success"></i> ' + element.textContent;
    } else if (
      text.includes("inativo") ||
      text.includes("inactive") ||
      text.includes("offline")
    ) {
      element.classList.add("status-inactive");
      element.innerHTML =
        '<i class="fas fa-circle text-secondary"></i> ' + element.textContent;
    } else if (
      text.includes("pendente") ||
      text.includes("pending") ||
      text.includes("manutençao") ||
      text.includes("maintenance")
    ) {
      element.classList.add("status-pending");
      element.innerHTML =
        '<i class="fas fa-circle text-warning"></i> ' + element.textContent;
    } else if (
      text.includes("erro") ||
      text.includes("error") ||
      text.includes("falha") ||
      text.includes("failed")
    ) {
      element.classList.add("status-error");
      element.innerHTML =
        '<i class="fas fa-circle text-danger"></i> ' + element.textContent;
    }
  });

  // Adicionar funcionalidade de busca rápida
  const searchInput = document.querySelector("#searchbar");
  if (searchInput) {
    searchInput.setAttribute(
      "placeholder",
      "Buscar... (Digite e pressione Enter)"
    );
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        this.form.submit();
      }
    });
  }

  // Melhorar tabelas com ordenação visual
  const tableHeaders = document.querySelectorAll("th.sortable a");
  tableHeaders.forEach(function (header) {
    header.addEventListener("click", function () {
      // Adicionar indicador de loading
      const loadingIcon = document.createElement("i");
      loadingIcon.className = "fas fa-spinner fa-spin ml-1";
      this.appendChild(loadingIcon);
    });
  });

  // Console log para debugging (apenas em desenvolvimento)
  if (
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1"
  ) {
    console.log("🏗️ SmartPark Admin - Jazzmin customizations loaded");
    console.log("Debug mode enabled for localhost");
  }
});

// Função global para atualizar estatísticas do dashboard
function updateDashboardStats() {
  const statsCards = document.querySelectorAll(".info-box");
  statsCards.forEach(function (card) {
    card.style.opacity = "0.7";
  });

  // Simular carregamento (pode ser substituído por AJAX real)
  setTimeout(function () {
    statsCards.forEach(function (card) {
      card.style.opacity = "1";
    });

    // Adicionar efeito de "novo dados"
    statsCards.forEach(function (card) {
      card.classList.add("updated");
      setTimeout(function () {
        card.classList.remove("updated");
      }, 1000);
    });
  }, 500);
}

// Adicionar estilos para animação de atualização
const style = document.createElement("style");
style.textContent = `
    .info-box.updated {
        animation: pulse 0.5s ease-in-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .focused {
        transition: all 0.2s ease;
    }
    
    .has-value label {
        color: #007bff;
        font-weight: 500;
    }
`;
document.head.appendChild(style);
