import { useEffect } from "react";

export default function PrettySeconds({ seconds }) {

    let numyears = Math.floor(seconds / 31536000);
    let numdays = Math.floor((seconds % 31536000) / 86400);
    let numhours = Math.floor(((seconds % 31536000) % 86400) / 3600);
    let numminutes = Math.floor((((seconds % 31536000) % 86400) % 3600) / 60);
    let numseconds = (((seconds % 31536000) % 86400) % 3600) % 60;

    let pretty ='';
    if (numyears > 0) {
        pretty += `${numyears.toFixed()} years, `
    }

    pretty += `${numdays.toFixed()} days, ${numhours.toFixed()} hours, ${numminutes.toFixed()} minutes, ${numseconds.toFixed()} seconds.`
    return <span>{pretty}</span>;
}
