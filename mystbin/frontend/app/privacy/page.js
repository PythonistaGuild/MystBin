"use client";
import Footer from "@/app/components/footer";


export default function Privacy() {
    return (
        <>
            <div className={"container"}>
                <div className={"navLimiter"}>
                    <div className={"navContainer"}>
                    </div>
                </div>

                <div className={"innerWrapper"}>
                    <div className={"termsContainer"}>
                            <h1>Privacy Policy</h1><br/><br/>

                        <b>This Privacy Policy applies to all personal information collected by MystBin via: </b><br/>
                            <div className={"termsList"}>
                                - https://mystb.in/<br/>
                                - https://beta.mystb.in/<br/>
                                - https://api.mystb.in/<br/><br/>
                            </div><br/>

                            <b>What information do we collect?</b><br/>
                            The personal information which we collect and hold about you may include:<br/><br/>
                            <div className={"termsList"}>
                                - email address<br/>
                                - ip addresses<br/>
                                - username & unique handle<br/>
                                - and user identifiers associated with third party logins including Google, Discord and GitHub.<br/><br/>
                            </div>

                            We may collect this information from you whenever you login to or visit the website.<br/>
                            We also collect cookies from you, which help customise your website experience. It is not possible to identify you personally from our use of cookies.<br/><br/>

                            The purpose for which we collect this information is to provide you with the best experience possible on the website.<br/><br/><br/>

                            <b>Passwords</b><br/>
                            All passwords you provide to MystBin are encrypted securely on our servers and are not known to anyone.
                            MystBin uses HTTPS to securely transfer data.
                        <br/>
                        <br/>
                        <b>Enquires</b><br/>
                            If you have any queries, or if you seek access to your personal information, or if you have a complaint about our privacy practices, you can contact us through:<br/>
                            <div className={"termsList"}>
                                <a href={"https://discord.gg/RAKc3HF"}>  - Discord</a>
                            </div>
                    </div>
                    <Footer />
                </div>
            </div>
        </>
    )
}
