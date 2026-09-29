function showLoading(form) {

    const button =
        form.querySelector(
            "button[type='submit']"
        );

    const loading =
        form.querySelector(
            "#loading"
        );

    if (button) {

        button.disabled = true;

        button.style.opacity =
            "0.65";

    }

    if (loading) {

        loading.classList.remove(
            "hidden"
        );

    }

}


async function copyPlan() {

    const plan =
        document.getElementById(
            "planText"
        );

    if (!plan) {
        return;
    }


    try {

        await navigator.clipboard
            .writeText(
                plan.innerText
            );


        const button =
            document.querySelector(
                ".section-heading .btn"
            );


        if (button) {

            const oldText =
                button.innerText;

            button.innerText =
                "Copied!";


            setTimeout(
                () => {

                    button.innerText =
                        oldText;

                },
                1200
            );

        }

    } catch (error) {

        alert(
            "Copy is not available."
        );

    }

}