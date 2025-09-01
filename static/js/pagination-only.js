// ** SCRIPT PAGINATION (offers.html, search.html)
(function() {
    "use strict";

    document.addEventListener("DOMContentLoaded", function() {
        const paginationWrapper = document.getElementById('pagination-wrapper');
        const productListWrapper = document.getElementById('product-list-wrapper');

        if (!paginationWrapper || !productListWrapper) {
            return;
        }

        console.log("Pagination-only script initialized.");

        /**
         * Met à jour le contenu de la page via AJAX.
         * @param {string} newPageQueryString - ex: "?page=2" ou "?"
         * @param {boolean} isLoadMore - True si on doit ajouter le contenu.
         */
        async function fetchAndUpdate(newPageQueryString, isLoadMore = false) {
            
            const baseUrl = window.location.pathname;
            
            const currentParams = new URLSearchParams(window.location.search);
            
            const newParams = new URLSearchParams(newPageQueryString);

            newParams.forEach((value, key) => {
                currentParams.set(key, value);
            });

            const finalQueryString = currentParams.toString();
            const apiUrl = `${baseUrl}?${finalQueryString}`;
            
            productListWrapper.classList.add('loading');

            try {
                const response = await fetch(apiUrl, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                if (!response.ok) throw new Error("Failed to fetch page content");

                const data = await response.json();
                
                if (isLoadMore) {
                    const container = productListWrapper.querySelector('.category__products-list');
                    if (container) {
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = data.html_products;
                        const newCards = tempDiv.querySelectorAll('.category__product');
                        newCards.forEach(card => container.appendChild(card));
                    }
                } else {
                    productListWrapper.innerHTML = data.html_products;
                }

                paginationWrapper.innerHTML = data.html_pagination;
                if (window.history.pushState) {
                    history.pushState({}, '', data.new_url);
                }
                const h1Element = document.getElementById('page-h1-title');
                if (h1Element && data.h1_title) {
                    h1Element.textContent = data.h1_title;
                }

            } catch (error) {
                console.error("Error during pagination:", error);
            } finally {
                productListWrapper.classList.remove('loading');
            }
        }

        paginationWrapper.addEventListener('click', function(event) {
            const paginationLink = event.target.closest('.js-pagination-link');
            const loadMoreButton = event.target.closest('.js-load-more-btn');

            if (paginationLink) {
                event.preventDefault();
                const pageQueryString = paginationLink.getAttribute('href');
                fetchAndUpdate(pageQueryString, false);
            }

            if (loadMoreButton) {
                event.preventDefault();
                const nextPage = loadMoreButton.dataset.nextPage;
                const pageQueryString = `?page=${nextPage}`;
                fetchAndUpdate(pageQueryString, true);
            }
        });
    });
})();