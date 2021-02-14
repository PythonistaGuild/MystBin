import {useRouter} from "next/router";
import {useEffect} from "react";

export default function SleeperPush({ ms, route }) {
    const router = useRouter()

    useEffect(() => {

        async function sleep() {
            const sleeper = new Promise(resolve => setTimeout(resolve, ms))
            await sleeper

            await router.push(route)
        }

        sleep();
    }, []);

    return (<div></div>)
}
