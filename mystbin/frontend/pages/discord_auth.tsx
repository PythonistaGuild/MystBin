import SleeperPush from "../components/Sleeper";

export default function DiscordAuth(props) {
    const {token} = props;
    return (
        <div>
        {token ? <SleeperPush ms={0} route={'/success'}/> : 'ERROR'}
        </div>);
}

export const getServerSideProps = async ({ query }) => {
    let response = await fetch('http://api:9000/users/connect/discord/',
        {method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(query)})

    const token = await response.json();

    return {props: { token }}
};
