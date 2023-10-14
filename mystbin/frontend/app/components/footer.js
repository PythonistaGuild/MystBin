import LogoSmall from "@/app/svgs/logoSmall";
import GithubLogo from "@/app/svgs/githubLogo";
import DiscordLogo from "@/app/svgs/discordLogo";


export default function Footer() {
    return (
        <div className={"footerContainer"}>
            <div className={"footerSection"}>
                <LogoSmall className={"logoSmall"} />
                <span>MystBin - Copyright © 2020-current PythonistaGuild</span>
            </div>

            <div className={"footerRight"}>
                <div className={"footerSection"}>
                    <a href={`${process.env.NEXT_PUBLIC_BACKEND_HOST}/docs`}>Documentation</a>
                    <a href={"/privacy"}>Privacy Policy</a>
                    <a href={"https://discord.gg/RAKc3HF"}>Contact</a>
                </div>
                <div className={"footerSection"}>
                    <a href={"https://github.com/PythonistaGuild/"}><GithubLogo className={"socials"} /></a>
                    <a href={"https://discord.gg/RAKc3HF"}><DiscordLogo className={"socials"} /></a>
                </div>
            </div>
        </div>
    )
}