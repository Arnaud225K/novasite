
/**
 * Utility function for Russian noun pluralization.
 */
function getNounPluralForm(number, one, few, many) {
    try {
        let n = Math.abs(parseInt(number, 10)) % 100;
        let lastDigit = n % 10;
        if (n > 10 && n < 20) return many;
        if (lastDigit > 1 && lastDigit < 5) return few;
        if (lastDigit === 1) return one;
    } catch (e) { return many; }
    return many;
}

/**
 * Met à jour le compteur du panier dans le header.
 * Cette fonction est attachée à 'window' pour être accessible globalement.
 * @param {number} count - Le nouveau nombre d'articles uniques.
 */
window.updateHeaderCartCounter = function(count) {
    const counterElement = document.getElementById('header-cart-count');
    if (!counterElement) {
        return;
    }

    const itemCount = parseInt(count, 10) || 0;
    
    counterElement.textContent = itemCount;
    
    if (itemCount > 0) {
        counterElement.classList.remove('hidden');
    } else {
        counterElement.classList.add('hidden');
    }
};


document.addEventListener('DOMContentLoaded', function() {

    // --- Délégation d'événements pour l'AJOUT AU PANIER ---
    document.body.addEventListener('click', async function(event) {
        const addButton = event.target.closest('.js-add-to-cart');
        if (addButton) {
            event.preventDefault();
            const productId = addButton.dataset.productId;
            if (!productId) { console.error("Product ID missing."); return; }
            
            const url = `/checkout/cart/add/${productId}/`;
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfInput) { console.error("CSRF token not found."); return; }

            addButton.textContent = 'Добавляем...';
            addButton.disabled = true;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfInput.value },
                    body: JSON.stringify({ quantity: 1 }),
                });
                const data = await response.json();

                if (data.success) {
                    // Mettre à jour tous les boutons et cartes pour ce produit
                    document.querySelectorAll(`.js-add-to-cart[data-product-id="${productId}"]`).forEach(btn => {
                        btn.textContent = 'В корзине';
                        btn.classList.add('in-cart');
                        btn.classList.add('purchased')
                        btn.disabled = false;
                    });
                    document.querySelectorAll(`.category__product[data-product-id="${productId}"], .product-card[data-product-id="${productId}"]`).forEach(card => {
                        card.classList.add('purchased');
                    });
                    
                    // Mettre à jour le compteur du header
                    updateHeaderCartCounter(data.cart_unique_items_count);
                } else {
                    addButton.textContent = 'Ошибка';
                }
            } catch (error) {
                console.error("Failed to add product to cart:", error);
                addButton.textContent = 'Ошибка';
                addButton.disabled = false;
            }
        }
    });


    const mainContent = document.querySelector('main.ajax-category');
    if (!mainContent) return;

    const productListWrapper = document.getElementById('product-list-wrapper');
    const paginationWrapper = document.getElementById('pagination-wrapper');
    const filtersWrapper = document.getElementById('filters-wrapper');
    const activeFiltersWrapper = document.getElementById('active-filters-wrapper');

    const baseApiUrl = mainContent.dataset.apiUrl;

    // HELPER FUNCTIONS
    function buildFilterSegmentFromForm() {
        const form = document.getElementById('filters-form');
        if (!form) return '';
        const activeFilters = {};
        form.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
            const name = cb.name;
            const value = cb.value;
            if (!activeFilters[name]) { activeFilters[name] = new Set(); }
            activeFilters[name].add(value);
        });
        const sortedKeys = Object.keys(activeFilters).sort();
        if (sortedKeys.length === 0) return '';
        const parts = sortedKeys.map(key => {
            const values = Array.from(activeFilters[key]).sort();
            return `${key}=${values.map(v => encodeURIComponent(v)).join(',')}`;
        });
        return `f/${parts.join('/')}/`;
    }

    // CORE AJAX LOGIC
    async function fetchAndReplaceContent(pageQueryString = '') {
        if (!baseApiUrl) {
            console.error("The data-api-url attribute is missing. Cannot make API calls.");
            return;
        }
        
        productListWrapper.classList.add('loading');
        if (filtersWrapper) filtersWrapper.classList.add('loading');
        if (activeFiltersWrapper) activeFiltersWrapper.classList.add('loading');
        
        const filterSegment = buildFilterSegmentFromForm();
        const apiUrl = `${baseApiUrl.replace(/\/$/, '')}/${filterSegment}${pageQueryString}`;

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`Network error: ${response.statusText}`);
            const data = await response.json();

            if (productListWrapper) productListWrapper.innerHTML = data.html_products;
            if (paginationWrapper) paginationWrapper.innerHTML = data.html_pagination;
            if (filtersWrapper && data.html_filters) filtersWrapper.innerHTML = data.html_filters;
            if (activeFiltersWrapper && data.html_active_filters !== undefined) activeFiltersWrapper.innerHTML = data.html_active_filters;

            const h1Element = document.getElementById('page-h1-title');
            if (h1Element && data.h1_title) h1Element.textContent = data.h1_title;
            const countDisplayElement = document.getElementById('product-count-display');
            if (countDisplayElement && data.product_count !== undefined) {
                const count = data.product_count;
                const pluralWord = getNounPluralForm(count, 'наименование', 'наименования', 'наименований');
                countDisplayElement.textContent = `Найдено ${count} ${pluralWord}`;
            }

            if (window.history.pushState) {
                history.pushState({}, '', data.new_url);
            }
            
            if (filtersWrapper) {
                initFilterFeatures();
            }
        } catch (error) {
            console.error("Error updating content:", error);
        } finally {
            productListWrapper.classList.remove('loading');
            if (filtersWrapper) filtersWrapper.classList.remove('loading');
            if (activeFiltersWrapper) activeFiltersWrapper.classList.remove('loading');
        }
    }

    async function loadMoreProducts(button) {
        const nextPage = button.dataset.nextPage;
        if (!nextPage) return;
        button.textContent = 'Загрузка...';
        button.disabled = true;

        const filterSegment = buildFilterSegmentFromForm();
        const apiUrl = `${baseApiUrl.replace(/\/$/, '')}/${filterSegment}?page=${nextPage}`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) throw new Error(`Network error: ${response.statusText}`);
            const data = await response.json();
            
            const productListContainer = productListWrapper.querySelector('.category__products-list');
            if (productListContainer) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.html_products;
                const newProductCards = tempDiv.querySelectorAll('.category__product');
                newProductCards.forEach(card => productListContainer.appendChild(card));
            } else {
                console.error("[Load More] Could not find '.category__products-list' to append new products.");
            }

            const h1Element = document.getElementById('page-h1-title');
            if (h1Element && data.h1_title) h1Element.textContent = data.h1_title;
            
            paginationWrapper.innerHTML = data.html_pagination;
            if (window.history.pushState) {
                history.pushState({}, '', data.new_url);
            }
        } catch (error) {
            console.error("Error loading more products:", error);
            const currentButton = paginationWrapper.querySelector('.js-load-more-btn');
            if (currentButton) {
                currentButton.textContent = 'Ошибка. Попробовать еще?';
                currentButton.disabled = false;
            }
        }
    }

    // INITIALIZATION & EVENT LISTENERS
    mainContent.addEventListener('click', async function(event) {
        
        // -- Logique de PAGINATION --
        const paginationLink = event.target.closest('.js-pagination-link');
        if (paginationLink) {
            event.preventDefault();
            const pageQueryString = paginationLink.getAttribute('href');
            fetchAndReplaceContent(pageQueryString);
        }

        const loadMoreButton = event.target.closest('.js-load-more-btn');
        if (loadMoreButton) {
            event.preventDefault();
            loadMoreProducts(loadMoreButton);
        }

        // -- Logique de RESET des filtres --
        const resetButton = event.target.closest('.js-reset-filters-btn');
        if (resetButton) {
            event.preventDefault();
            const form = document.getElementById('filters-form');
            if (form) {
                form.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
                    cb.checked = false;
                    if(typeof updateSingleFilterCount === "function") updateSingleFilterCount(cb);
                });
            }
            fetchAndReplaceContent();
        }

        // -- Logique de suppression d'un TAG de filtre actif --
        const removeButton = event.target.closest('.js-remove-filter-btn');
        if (removeButton) {
            event.preventDefault();
            const groupSlug = removeButton.dataset.groupSlug;
            const valueSlug = removeButton.dataset.valueSlug;
            const checkbox = document.querySelector(`#filters-form input[name="${groupSlug}"][value="${valueSlug}"]`);
            if (checkbox && checkbox.checked) {
                checkbox.checked = false;
                if(typeof updateSingleFilterCount === "function") updateSingleFilterCount(checkbox);
                fetchAndReplaceContent();
            }
        }
    });

    // --- Initialisation et écouteurs spécifiques aux filtres ---
    if (filtersWrapper) {
        
        function initFilterDropdowns() {
            filtersWrapper.querySelectorAll(".filters__box-item").forEach(item => {
                item.addEventListener("mousedown", e => {
                    const dropdown = e.currentTarget.querySelector(".filters__dropdown");
                    if (dropdown && !e.target.closest('.filters__dropdown')) {
                        const wasOpen = e.currentTarget.classList.contains("open");
                        filtersWrapper.querySelectorAll(".filters__box-item.open").forEach(openItem => {
                            if (openItem !== e.currentTarget) {
                                openItem.classList.remove("open");
                                openItem.querySelector(".filters__dropdown").classList.add("hidden");
                            }
                        });
                        e.currentTarget.classList.toggle("open", !wasOpen);
                        dropdown.classList.toggle("hidden", wasOpen);
                    }
                });
            });
            filtersWrapper.querySelectorAll(".filters__dropdown").forEach(dropdown => {
                dropdown.addEventListener('mousedown', e => e.stopPropagation());
            });
        }
        function initFilterSearch() {
            filtersWrapper.querySelectorAll('.filter-search').forEach(input => {
                input.addEventListener('input', event => {
                    const searchTerm = event.target.value.toLowerCase().trim();
                    const valueList = event.target.closest('.filters__dropdown').querySelector('.filter-values-list');
                    const noResultsMessage = valueList.querySelector('.filter-no-results-message');
                    const labels = valueList.querySelectorAll('label');
                    let visibleCount = 0;
                    labels.forEach(label => {
                        const isVisible = label.textContent.toLowerCase().trim().includes(searchTerm);
                        label.classList.toggle('hidden-by-search', !isVisible);
                        if (isVisible) visibleCount++;
                    });
                    if (noResultsMessage) {
                        noResultsMessage.style.display = visibleCount === 0 ? 'block' : 'none';
                    }
                });
                input.addEventListener('mousedown', e => e.stopPropagation());
            });
        }

        function updateSingleFilterCount(checkbox) {
            const filterBoxItem = checkbox.closest('.filters__box-item');
            if (!filterBoxItem) return;
            const titleSpan = filterBoxItem.querySelector('span:first-child');
            if (!titleSpan) return;
            const checkedCount = filterBoxItem.querySelectorAll('input[type="checkbox"]:checked').length;
            let countSpan = titleSpan.querySelector('.filter-count');
            if (checkedCount > 0) {
                if (!countSpan) {
                    countSpan = document.createElement('span');
                    countSpan.className = 'filter-count';
                    titleSpan.appendChild(countSpan);
                }
                countSpan.textContent = ` (${checkedCount})`;
            } else if (countSpan) {
                countSpan.remove();
            }
        }

        function initFilterFeatures() {
            initFilterDropdowns();
            initFilterSearch();
        }
        
        initFilterFeatures();

        filtersWrapper.addEventListener('change', event => {
            if (event.target.tagName === 'INPUT' && event.target.type === 'checkbox') {
                updateSingleFilterCount(event.target);
                fetchAndReplaceContent();
            }
        });

    } else {
        console.log("No filter section (#filters-wrapper) was detected. Filter-specific features are not initialized.");
    }
});





document.addEventListener('DOMContentLoaded', function(){

    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        const fileInput = checkoutForm.querySelector('input[name="file"]');
        const fileNameDisplay = document.getElementById('file-name-display');

        // Afficher le nom du fichier sélectionné
        if (fileInput && fileNameDisplay) {
            fileInput.addEventListener('change', function() {
                if (this.files && this.files.length > 0) {
                    fileNameDisplay.textContent = this.files[0].name;
                } else {
                    fileNameDisplay.textContent = 'Прикрепить файл';
                }
            });
        }

        // Lier les checkboxes d'accord
        const agreementVisual = document.getElementById('agreement_visual_checkbox');
        const agreementHidden = document.querySelector('input[name="agreement"]');
        if (agreementVisual && agreementHidden) {
            agreementVisual.addEventListener('change', () => {
                agreementHidden.checked = agreementVisual.checked;
            });
        }

        // Validation avant la soumission
        checkoutForm.addEventListener('submit', function(event) {
            let isFormValid = true;

            // --- Validation du téléphone ---
            const phoneInput = checkoutForm.querySelector('input[name="phone"]');
            const phoneValue = phoneInput.value.replace(/\D/g, ''); // clean le numéro
            const phoneRegex = /^7\d{10}$/;
            let finalPhone = phoneValue;
            if (phoneValue.startsWith('8') && phoneValue.length === 11) {
                finalPhone = '7' + phoneValue.substring(1);
            }
            
            if (!phoneRegex.test(finalPhone)) {
                // Affichez une erreur
                isFormValid = false;
            }

            // --- Validation du fichier ---
            if (fileInput && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                const MAX_SIZE_JS = 5 * 1024 * 1024; // Doit correspondre au backend
                const ALLOWED_EXT_JS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.webp', '.gif', '.txt', '.rtf'];
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                if (file.size > MAX_SIZE_JS) {
                    isFormValid = false;
                }
                if (!ALLOWED_EXT_JS.includes(fileExt)) {
                    isFormValid = false;
                }
            }

            // --- Validation agreement ---
            if (!agreementVisual.checked) {
                isFormValid = false;
            }

            if (!isFormValid) {
                event.preventDefault();
                console.log('Form client is invalid from the frontend');
            }
        });
    }    

});



// MODULE DE GESTION DES FORMULAIRES (MODALES)
(function() {
    "use strict";

    // --- Fonctions de Validation Côté Client ---
    function displayValidationError(input, message, errorClass) {
        const form = input.closest('form');
        if (!form) return;
        const errorContainer = form.querySelector(errorClass);
        if (errorContainer) {
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
        }
        input.classList.add('invalid');
    }
    function clearValidationError(input, errorClass) {
        const form = input.closest('form');
        if (!form) return;
        const errorContainer = form.querySelector(errorClass);
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
        input.classList.remove('invalid');
    }
    function validatePhoneNumber(form) {
        const phoneInput = form.querySelector('input[name="phone"]');
        if (!phoneInput) return true;
        const cleanedPhone = phoneInput.value.replace(/\D/g, '');
        if (phoneInput.required && cleanedPhone.length < 11) {
            displayValidationError(phoneInput, 'Неверный формат номера телефона.', '.phone-error');
            return false;
        }
        clearValidationError(phoneInput, '.phone-error');
        return true;
    }
    function validateEmail(form) {
        const emailInput = form.querySelector('input[name="email"]');
        if (!emailInput) return true;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (emailInput.value && !emailRegex.test(emailInput.value)) {
            displayValidationError(emailInput, 'Неверный адрес электронной почты.', '.email-error');
            return false;
        }
        clearValidationError(emailInput, '.email-error');
        return true;
    }

    function validateAgreement(form) {
        const agreementCheckbox = form.querySelector('input[name="agreement"]');
        if (!agreementCheckbox) {
            return true;
        }

        const errorContainer = form.querySelector('.agreement-error');
        
        if (!agreementCheckbox.checked) {
            if (errorContainer) {
                errorContainer.textContent = 'Необходимо согласиться на обработку данных.';
                errorContainer.style.display = 'block';
            }
            return false;
        }
        
        if (errorContainer) {
            errorContainer.style.display = 'none';
        }
        return true;
    }

    // --- Fonction de soumission AJAX ---
    async function handleFormSubmit(form) {
        const submitButton = form.querySelector('.submit-form-btn, .btn[type="submit"]');
        const errorContainer = form.querySelector('.js-error');
        const url = form.getAttribute('action');
        const formData = new FormData(form);

        if (submitButton) submitButton.disabled = true;
        if (errorContainer) errorContainer.style.display = 'none';

        try {
            const response = await fetch(url, { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } });
            const data = await response.json();
            if (response.ok && data.success) {
                if (data.thank_you_url) window.location.href = data.thank_you_url;
            } else {
                const errorMessage = data.error || "Пожалуйста, исправьте ошибки.";
                if (errorContainer) {
                    errorContainer.textContent = errorMessage;
                    errorContainer.style.display = 'block';
                }
            }
        } catch (error) {
            console.error("AJAX form submission error:", error);
            if (errorContainer) {
                errorContainer.textContent = "Произошла ошибка сети. Попробуйте снова.";
                errorContainer.style.display = 'block';
            }
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    }

    // --- Initialisation ---
    document.addEventListener("DOMContentLoaded", function() {
        // Appliquer le masque de téléphone
        document.querySelectorAll('input[data-phone]').forEach(input => {
            function mask(event) {
                let keyCode; event.keyCode && (keyCode = event.keyCode);
                let pos = this.selectionStart;
                if (pos < 3) event.preventDefault();
                let matrix = "+7 (___) ___-__-__", i = 0, def = matrix.replace(/\D/g, ""), val = this.value.replace(/\D/g, ""),
                new_value = matrix.replace(/[_\d]/g, a => (i < val.length ? val.charAt(i++) || def.charAt(i) : a));
                i = new_value.indexOf("_");
                if (i != -1) { i < 5 && (i = 3); new_value = new_value.slice(0, i) }
                let reg = matrix.substr(0, this.value.length).replace(/_+/g, a => "\\d{1," + a.length + "}").replace(/[+()]/g, "\\$&");
                reg = new RegExp("^" + reg + "$");
                if (!reg.test(this.value) || this.value.length < 5 || keyCode > 47 && keyCode < 58) this.value = new_value;
                if (event.type == "blur" && this.value.length < 5) this.value = "";
            }
            input.addEventListener("input", mask, false);
            input.addEventListener("focus", mask, false);
            input.addEventListener("blur", mask, false);
            input.addEventListener("keydown", mask, false);
        });

        document.querySelectorAll('.modal__form').forEach(form => {
            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const isPhoneValid = validatePhoneNumber(this);
                const isEmailValid = validateEmail(this);
                const isAgreementValid = validateAgreement(this);

                if (isPhoneValid && isEmailValid && isAgreementValid) {
                    handleFormSubmit(this);
                }
            });
        });
    });
})();




document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('[data-micromodal-trigger="service-modal"]').forEach(button => {
        button.addEventListener('click', function() {
            
            const serviceName = this.dataset.serviceName;
            
            if (!serviceName) {
                console.warn("Le bouton n'a pas d'attribut data-service-name.");
                return;
            }

            const modal = document.getElementById('service-modal');
            if (!modal) {
                console.error("La modale avec l'ID 'service-modal' est introuvable.");
                return;
            }

            const modalTitle = modal.querySelector('#service-modal-title');
            const commentInput = modal.querySelector('#service-comment-input');
            
            if (modalTitle) {
                modalTitle.textContent = `Заявка на услугу: «${serviceName}»`;
            }
            
            if (commentInput) {
                commentInput.value = `Запрос по услуге: ${serviceName}`;
            }
            
            console.log(`Modal updated for service: "${serviceName}"`);
        });
    });
});




document.addEventListener('DOMContentLoaded', function() {
    
    const catalogLink = document.querySelector('.subheader__catalog');
    const headerMenu = document.querySelector('.header-menu');

    if (!catalogLink || !headerMenu) {
        console.warn("Could not find catalog trigger or menu container.");
        return;
    }

    function initializeTabs() {
        const tablinks = headerMenu.querySelectorAll('.tablink');
        const tabcontents = headerMenu.querySelectorAll('.tabcontent');

        if (tablinks.length === 0) return;

        tablinks.forEach(tab => {
            tab.addEventListener('mouseenter', function() {
                tablinks.forEach(t => t.classList.remove('active'));
                tabcontents.forEach(t => t.classList.remove('active'));
                
                this.classList.add('active');
                const targetId = this.getAttribute('data-target');
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    targetElement.classList.add('active');
                }
            });
        });

        tablinks[0].classList.add('active');
        const firstTargetId = tablinks[0].getAttribute('data-target');
        if (firstTargetId) {
            const firstTargetElement = document.getElementById(firstTargetId);
            if(firstTargetElement) firstTargetElement.classList.add('active');
        }
    }

    async function loadMenuContentIfNeeded() {
        if (headerMenu.dataset.menuLoaded === 'true') {
            return;
        }
        
        console.log("Loading mega menu content via AJAX...");
        headerMenu.classList.add('loading');

        try {
            const response = await fetch("/ajax/get-mega-menu/", {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            }); 
            
            if (!response.ok) throw new Error("Failed to fetch menu");
            
            const htmlContent = await response.text();
            
            headerMenu.innerHTML = htmlContent;
            headerMenu.dataset.menuLoaded = 'true';
            headerMenu.classList.remove('loading');

            initializeTabs();

        } catch (error) {
            console.error("Error loading mega menu:", error);
            headerMenu.innerHTML = '<p style="padding: 20px; color: red;">Ошибка загрузки меню.</p>';
            headerMenu.classList.remove('loading');
        }
    }

    
    catalogLink.addEventListener('mouseenter', function() {
        loadMenuContentIfNeeded();
        headerMenu.classList.add('opened');
    });
    
    function handleMouseLeave(event) {
        const relatedTarget = event.relatedTarget;
        if (!headerMenu.contains(relatedTarget) && !catalogLink.contains(relatedTarget)) {
            headerMenu.classList.remove('opened');
        }
    }
    
    catalogLink.addEventListener('mouseleave', handleMouseLeave);
    headerMenu.addEventListener('mouseleave', handleMouseLeave);
    
    document.addEventListener('click', function(e) {
        if (!catalogLink.contains(e.target) && !headerMenu.contains(e.target)) {
            headerMenu.classList.remove('opened');
        }
    });
});



// MODULE DE GESTION DU CONSENTEMENT AUX COOKIES
(function() {
    "use strict";

    const COOKIE_NAME = 'user_cookie_consent';
    const BANNER_ID = 'cookies-banner';

    function setCookie(name, value, options = {}) {
        if (options.days) {
            let date = new Date();
            date.setTime(date.getTime() + (options.days * 24 * 60 * 60 * 1000));
            options.expires = date.toUTCString();
        }
        try {
            const mainDomain = window.location.hostname.split('.').slice(-2).join('.');
            if (mainDomain !== 'localhost' && !/^\d+\.\d+\.\d+\.\d+$/.test(mainDomain)) {
                options.domain = `.${mainDomain}`;
            }
        } catch(e) {
            console.warn("[Cookies] Could not determine main domain.");
        }
        options.path = '/';
        let updatedCookie = encodeURIComponent(name) + "=" + encodeURIComponent(value);
        for (let optionKey in options) {
            updatedCookie += "; " + optionKey;
            let optionValue = options[optionKey];
            if (optionValue !== true) {
                updatedCookie += "=" + optionValue;
            }
        }
        document.cookie = updatedCookie;
    }

    function getCookie(name) {
        const matches = document.cookie.match(new RegExp(
            "(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
        ));
        return matches ? decodeURIComponent(matches[1]) : null;
    }
    
    function initializeCookieBanner() {

        const banner = document.getElementById(BANNER_ID);
        if (!banner) {
            return;
        }

        const acceptButtons = banner.querySelectorAll('.accept-cookies');
        if (acceptButtons.length === 0) {
            return;
        }

        if (getCookie(COOKIE_NAME) === 'accepted') {
            banner.style.display = 'none';
            return;
        }

        banner.style.display = 'block';

        acceptButtons.forEach(button => {
            button.addEventListener('click', function(event) {
                event.preventDefault();
                
                setCookie(COOKIE_NAME, 'accepted', { days: 365 });
                
                banner.style.display = 'none';
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeCookieBanner);
    } else {
        initializeCookieBanner();
    }

})();


// ================================================================
// MODULE DE RECHERCHE "LIVE"
// ================================================================

// function initializeLiveSearch() {
//     const searchContainer = document.querySelector(".header__actions");
//     if (!searchContainer) return;

//     const searchForm = searchContainer.querySelector('form');
//     const searchInput = searchContainer.querySelector('input[type="search"]');
//     const resultsDropdown = document.getElementById('live-search-results');
//     const openButton = searchContainer.querySelector('.search');
//     const closeButton = searchContainer.querySelector('.search-close');
    
//     if (!searchInput || !resultsDropdown || !openButton || !closeButton) return;

//     // --- Logique pour ouvrir/fermer la barre de recherche ---
//     openButton.addEventListener("click", e => {
//         if (!searchContainer.classList.contains("search-visible")) {
//             e.preventDefault(); // Empêche la soumission du formulaire
//             searchContainer.classList.add("search-visible");
//             searchInput.focus();
//         }
//     });
//     closeButton.addEventListener("click", () => {
//         searchContainer.classList.remove("search-visible");
//         resultsDropdown.style.display = 'none';
//     });
//     document.addEventListener("click", e => {
//         if (!searchContainer.contains(e.target)) {
//             searchContainer.classList.remove("search-visible");
//             resultsDropdown.style.display = 'none';
//         }
//     });

//     // --- Logique de recherche asynchrone ---
//     let searchTimeout;

//     searchInput.addEventListener('input', () => {
//         const query = searchInput.value.trim();
//         clearTimeout(searchTimeout);

//         if (query.length < 3) {
//             resultsDropdown.style.display = 'none';
//             return;
//         }

//         searchTimeout = setTimeout(async () => {
//             const url = `/search/live-api/?q=${encodeURIComponent(query)}`;
//             try {
//                 const response = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
//                 const data = await response.json();
//                 renderSearchResults(data.results, query);
//             } catch (error) {
//                 console.error("Live search error:", error);
//             }
//         }, 300);
//     });

//     /**
//      * Affiche les résultats de la recherche dans le dropdown.
//      */
//     function renderSearchResults(results, query) {
//         let html = '';
//         if (results.length === 0) {
//             html = '<div class="no-results">Ничего не найдено</div>';
//         } else {
//             html = results.map(item => `
//                 <a href="${item.url}" class="search-result-item">
//                     <div class="search-result-item__image">
//                         ${item.image_url ? `<img src="${item.image_url}" alt="">` : '<div class="placeholder"></div>'}
//                     </div>
//                     <div class="search-result-item__info">
//                         <span class="title">${item.title}</span>
//                         <span class="type">${item.type === 'product' ? 'Товар' : 'Категория'}</span>
//                     </div>
//                 </a>
//             `).join('');
//         }
        
//         // On ajoute un lien "Voir tous les résultats"
//         const fullSearchUrl = `${searchForm.getAttribute('action')}?q=${encodeURIComponent(query)}`;
//         html += `<a href="${fullSearchUrl}" class="search-result-all">Все результаты</a>`;

//         resultsDropdown.innerHTML = html;
//         resultsDropdown.style.display = 'block';
//     }
// }

// document.addEventListener('DOMContentLoaded', function() {
//     initializeLiveSearch();
// });



function initializeLiveSearch() {
    const searchContainer = document.querySelector(".header__actions");
    if (!searchContainer) return;

    const searchForm = searchContainer.querySelector('form');
    const searchInput = searchContainer.querySelector('input[type="search"]');
    const resultsDropdown = document.getElementById('live-search-results');
    const openButton = searchContainer.querySelector('.search');
    const closeButton = searchContainer.querySelector('.search-close');
    
    if (!searchInput || !resultsDropdown || !openButton || !closeButton) return;

    // --- Logique pour ouvrir/fermer la barre de recherche ---
    openButton.addEventListener("click", e => {
        if (!searchContainer.classList.contains("search-visible")) {
            e.preventDefault();
            searchContainer.classList.add("search-visible");
            searchInput.focus();
        }
    });

    closeButton.addEventListener("click", (e) => {
        e.preventDefault();
        searchContainer.classList.remove("search-visible");
        resultsDropdown.style.display = 'none';
        searchInput.value = '';
    });

    // Fermer la recherche quand on clique en dehors
    document.addEventListener("click", (e) => {
        if (!searchContainer.contains(e.target) && 
            !e.target.closest('.search-results-dropdown')) {
            searchContainer.classList.remove("search-visible");
            resultsDropdown.style.display = 'none';
        }
    });

    // Empêcher la fermeture quand on clique dans les résultats
    resultsDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // --- Logique de recherche asynchrone ---
    let searchTimeout;
    let currentRequest = null;

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim();
        clearTimeout(searchTimeout);

        // Annuler la requête précédente si elle est en cours
        if (currentRequest) {
            currentRequest.abort();
        }

        if (query.length < 2) {
            resultsDropdown.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(async () => {
            const url = `/search/live-api/?q=${encodeURIComponent(query)}`;
            
            try {
                const controller = new AbortController();
                currentRequest = controller;
                
                const response = await fetch(url, { 
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                    signal: controller.signal
                });
                
                if (!response.ok) throw new Error('Network response was not ok');
                
                const data = await response.json();
                renderSearchResults(data.results, query);
                
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error("Live search error:", error);
                    resultsDropdown.innerHTML = '<div class="no-results">Ошибка загрузки</div>';
                    resultsDropdown.style.display = 'block';
                }
            } finally {
                currentRequest = null;
            }
        }, 300);
    });

    // Navigation au clavier
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchContainer.classList.remove("search-visible");
            resultsDropdown.style.display = 'none';
        }
    });

    /**
     * Affiche les résultats de la recherche dans le dropdown.
     */
    function renderSearchResults(results, query) {
        if (!query || query.length < 2) {
            resultsDropdown.style.display = 'none';
            return;
        }

        let html = '';
        if (results.length === 0) {
            html = '<div class="no-results">Ничего не найдено</div>';
        } else {
            html = results.slice(0, 8).map(item => `
                <a href="${item.url}" class="search-result-item">
                    <div class="search-result-item__image">
                        ${item.image_url ? `<img src="${item.image_url}" alt="${item.title}" loading="lazy">` : '<div class="placeholder">📦</div>'}
                    </div>
                    <div class="search-result-item__info">
                        <span class="title">${highlightText(item.title, query)}</span>
                        <span class="type">${item.type === 'product' ? 'Товар' : 'Категория'}</span>
                    </div>
                </a>
            `).join('');
        }
        
        // Lien "Voir tous les résultats"
        const fullSearchUrl = `${searchForm.getAttribute('action')}?q=${encodeURIComponent(query)}`;
        html += `<a href="${fullSearchUrl}" class="search-result-all">Показать все результаты (${results.length})</a>`;

        resultsDropdown.innerHTML = html;
        resultsDropdown.style.display = 'block';
    }

    /**
     * Met en évidence le texte correspondant à la recherche
     */
    function highlightText(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
}

// Styles pour le texte en surbrillance
const highlightStyle = document.createElement('style');
highlightStyle.textContent = `
    mark {
        background: linear-gradient(120deg, #ffeb3b33, #ffeb3b4d);
        color: inherit;
        padding: 0 2px;
        border-radius: 2px;
    }
`;
document.head.appendChild(highlightStyle);

document.addEventListener('DOMContentLoaded', function() {
    initializeLiveSearch();
});