import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";

const PostMonacoEditor = dynamic(() => import("../components/EditorTabs"), {
  ssr: false,
});

export default function Home() {
  return (
    <div>
      <Head>
        <title>MystBin</title>
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Base className={styles.Tabs}>
        <PostMonacoEditor />
      </Base>
    </div>
  );
}
