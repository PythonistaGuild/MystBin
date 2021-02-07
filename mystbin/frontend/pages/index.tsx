import Head from "next/head";
import dynamic from "next/dynamic";
import Base from "../components/Base";
import styles from "../styles/Home.module.css";
import { PropsWithoutRef } from "react";
import { GetServerSideProps } from "next";
import AES from "crypto-js/aes";

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
