document.addEventListener(
    "DOMContentLoaded",
    () => {

        const forms =
            document.querySelectorAll("form");


        forms.forEach(
            (form) => {

                form.addEventListener(
                    "submit",
                    () => {

                        const button =
                            form.querySelector(
                                "button[type='submit'], button:not([type])"
                            );


                        if (
                            button &&
                            !form.action.includes(
                                "admin-login"
                            )
                        ) {

                            button.disabled = true;

                            button.dataset.originalText =
                                button.textContent;

                            button.textContent =
                                "Gemini is generating…";
                        }

                    }
                );

            }
        );

    }
);