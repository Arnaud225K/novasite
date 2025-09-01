(() => {
    "use strict";

    document.addEventListener("DOMContentLoaded", () => {
        
        const cartPageContainer = document.querySelector('.cartpage');
        if (!cartPageContainer) {
            return;
        }

        console.log("Cart page detected. Initializing cart-specific logic.");

        // FONCTIONS UTILITAIRES

        function getTovarPlural(count) {
            try {
                count = Math.abs(parseInt(count, 10)) % 100;
                const lastDigit = count % 10;
                if (count > 10 && count < 20) return "ов";
                if (lastDigit > 1 && lastDigit < 5) return "а";
                if (lastDigit === 1) return "";
            } catch (e) {
                return "ов";
            }
            return "ов";
        }

        function displayValidationError(input, message) {
            const formGroup = input.closest('.form-group, .form-block__agreement > label');
            if (!formGroup) return;
            let errorContainer = formGroup.parentElement.querySelector('.form-error');
            if (!errorContainer) {
                errorContainer = document.createElement('div');
                errorContainer.className = 'form-error';
                formGroup.insertAdjacentElement('afterend', errorContainer);
            }
            errorContainer.textContent = message;
            errorContainer.style.display = 'block';
            input.classList.add('invalid');
        }

        function clearValidationError(input) {
            const formGroup = input.closest('.form-group, .form-block__agreement > label');
            if (!formGroup) return;
            const errorContainer = formGroup.parentElement.querySelector('.form-error');
            if (errorContainer) {
                errorContainer.style.display = 'none';
            }
            input.classList.remove('invalid');
        }


        // // --- updateCartUI ---

        function updateCartUI(data) {
            const itemsContainer = document.getElementById('cart-items-container');
            if (itemsContainer && data.html_cart_items !== undefined) {
                itemsContainer.innerHTML = data.html_cart_items;
            }

            const totalItemsElement = document.getElementById('cart-summary-count');
            const summaryPriceElement = document.getElementById('cart-summary-price');
            const totalPriceElement = document.getElementById('cart-total-price');
            
            const uniqueItemsCount = data.cart_unique_items_count !== undefined ? parseInt(data.cart_unique_items_count, 10) : null;

            if (totalItemsElement && uniqueItemsCount !== null) {
                totalItemsElement.textContent = `${uniqueItemsCount} товар${getTovarPlural(uniqueItemsCount)}`;
            }
            if (summaryPriceElement && data.cart_total_price_display !== undefined) {
                summaryPriceElement.textContent = data.cart_total_price_display;
            }
            if (totalPriceElement && data.cart_total_price_display !== undefined) {
                totalPriceElement.textContent = data.cart_total_price_display;
            }

            const emptyMessage = document.getElementById('cart-empty-message');
            const contentWrapper = document.getElementById('cart-content-wrapper');
            if (emptyMessage && contentWrapper && uniqueItemsCount !== null) {
                const isCartEmpty = uniqueItemsCount === 0;
                emptyMessage.style.display = isCartEmpty ? 'block' : 'none';
                contentWrapper.style.display = isCartEmpty ? 'none' : 'block';
            }
        }
        
        // ================================================================
        // FONCTION AJAX GÉNÉRIQUE
        // ================================================================

        async function sendCartUpdateRequest(url, body = null) {
            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfInput) { console.error("CSRF token not found."); return; }

            const headers = { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': csrfInput.value };
            const options = { method: 'POST', headers };
            if (body) {
                options.body = JSON.stringify(body);
                headers['Content-Type'] = 'application/json';
            }
            
            try {
                const response = await fetch(url, options);
                if (!response.ok) throw new Error(`Network error: ${response.status}`);
                const data = await response.json();
                
                if (data.success) {
                    updateCartUI(data);
                    if (typeof window.updateHeaderCartCounter === 'function') {
                        window.updateHeaderCartCounter(data.cart_unique_items_count);
                    }
                } else {
                    console.error("API Error:", data.error);
                }
            } catch (error) {
                console.error("Failed to update cart:", error);
            }
        }

        // INITIALISATION DES ÉVÉNEMENTS
        
        // --- Gestion du formulaire de commande ---
        const checkoutForm = document.getElementById('checkout-form');
        if (checkoutForm) {
            const fileInput = checkoutForm.querySelector('input[name="file"]');
            const fileNameDisplay = document.getElementById('file-name-display');
            if (fileInput && fileNameDisplay) {
                fileInput.addEventListener('change', function() {
                    fileNameDisplay.textContent = this.files.length > 0 ? this.files[0].name : 'Прикрепить файл';
                });
            }
            
            const agreementVisual = document.getElementById('agreement_visual_checkbox');
            const agreementHidden = checkoutForm.querySelector('input[name="agreement"]');
            if (agreementVisual && agreementHidden) {
                agreementVisual.addEventListener('change', function() {
                    agreementHidden.checked = this.checked;
                    if (this.checked) {
                        clearValidationError(this);
                    }
                });
            }

            checkoutForm.addEventListener('submit', function(event) {
                let isFormValid = true;

                const phoneInput = checkoutForm.querySelector('input[name="phone"]');
                if (phoneInput) {
                    const cleanedPhone = phoneInput.value.replace(/\D/g, '');
                    if (cleanedPhone.length < 11) {
                        displayValidationError(phoneInput, "Пожалуйста, введите полный номер телефона.");
                        isFormValid = false;
                    } else {
                        clearValidationError(phoneInput);
                    }
                }

                if (agreementVisual && !agreementVisual.checked) {
                    displayValidationError(agreementVisual, "Необходимо согласиться на обработку данных.");
                    isFormValid = false;
                } else if (agreementVisual) {
                    clearValidationError(agreementVisual);
                }

                if (!isFormValid) {
                    event.preventDefault();
                    console.warn("Client-side form validation failed. Submission stopped.");
                }
            });
        }

        // --- Délégation d'événements pour les contrôles du panier ---
        const cartItemsContainer = document.getElementById('cart-items-container');
        if (cartItemsContainer) {
            cartItemsContainer.addEventListener('click', function(event) {
                const target = event.target;
                const cartItem = target.closest('.cartpage__item');
                if (!cartItem) return;

                const productId = cartItem.dataset.productId;
                const quantityInput = cartItem.querySelector(".cartpage__qty");
                if (!quantityInput) return;

                let currentQty = parseInt(quantityInput.value, 10);

                if (target.closest('.js-cart-qty-decrease, .left')) {
                    if (currentQty > 0) {
                        sendCartUpdateRequest(`/checkout/cart/update/${productId}/`, { quantity: currentQty - 1 });
                    }
                } else if (target.closest('.js-cart-qty-increase, .right')) {
                    sendCartUpdateRequest(`/checkout/cart/update/${productId}/`, { quantity: currentQty + 1 });
                } else if (target.closest('.js-cart-remove, .cartpage__item-del')) {
                    sendCartUpdateRequest(`/checkout/cart/remove/${productId}/`);
                }
            });

            cartItemsContainer.addEventListener('change', function(event) {
                const target = event.target;
                if (target.matches('.cartpage__qty, .js-cart-qty-input')) {
                    const cartItem = target.closest('.cartpage__item');
                    const productId = cartItem.dataset.productId;
                    let newQty = parseInt(target.value, 10);
                    if (isNaN(newQty) || newQty < 0) newQty = 0;
                    sendCartUpdateRequest(`/checkout/cart/update/${productId}/`, { quantity: newQty });
                }
            });
        }
    });
})();